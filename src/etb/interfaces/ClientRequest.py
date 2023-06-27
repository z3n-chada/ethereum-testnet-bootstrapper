"""
    Interfaces for sending and receiving requests and responses
    from CL and EL clients across the network.
"""

# TODO: we must pass the logger to get the correct log level from the caller module.
import logging
import time
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor, Future
from enum import Enum
from typing import Union, Awaitable, Dict

import requests
from requests import HTTPError

from ..config.ETBConfig import ClientInstance


class RequestType(str, Enum):
    BeaconAPIRequest = "BeaconAPIRequest"
    ExecutionRPCRequest = "ExecutionJSONRPCRequest"


class RequestProtocol(str, Enum):
    HTTP = "http"
    WS = "ws"


class ErrorResponse(Exception):
    """
        Some clients return 200 status code despite an error.
    """
    pass


class ClientInstanceRequest(object):
    """
        A client request is any message sent to a node that expects a response.
        This can be either JSONRPC for ELs, or BeaconAPI for CLs.
    """

    def __init__(self, payload: Union[dict, str], max_retries: int = 3, timeout: int = 5):
        """
        A request to a client instance.
        @param payload: the payload, a dictionary for JSONRPC, a string for BeaconAPI.
        @param max_retries: max number of retries before bailing.
        @param timeout: timeout to use per request.
        """
        self.payload: Union[dict, str] = payload
        self.logger = logging.getLogger()
        self.max_retries: int = max_retries
        self.timeout: int = timeout

    @abstractmethod
    def perform_request(self, instance: ClientInstance) -> Union[Exception, requests.Response]:
        """
            Either returns the response or an exception.
        """
        pass

    def is_valid(self, response: Union[requests.Response, Exception]) -> bool:
        """
        Check if the response is valid.
        @param response: the response/exception returned from perform_request.
        @return:
        """
        return not isinstance(response, Exception)


class ExecutionJSONRPCRequest(ClientInstanceRequest):
    def __init__(self, payload: dict, max_retries: int = 3, timeout: int = 5):
        super().__init__(payload=payload, max_retries=max_retries, timeout=timeout)

    def perform_request(self, instance: ClientInstance) -> Union[Exception, requests.Response]:
        """
        Perform a request to the execution client. Either return an exception or a response.
        In the case that the response is an error code we also return an exception. (besu
        workaround)
        @param instance: client instance to send the request to.
        @return: response on success, exception otherwise.
        """
        json_rpc_endpoint = instance.get_execution_jsonrpc_path()
        for attempt in range(self.max_retries):
            try:
                response = requests.post(json_rpc_endpoint, json=self.payload, timeout=self.timeout)
                response.raise_for_status()  # raise an exception based on the response.
                data = response.json()
                if "error" in data:
                    raise ErrorResponse(data["error"])
                # response is good, optionally process data here.
                return response

            except (requests.exceptions.RequestException, HTTPError) as e:
                if attempt < self.max_retries - 1:
                    self.logger.debug(f"{e.strerror} occurred during the API request {json_rpc_endpoint}. Retrying...")
                else:
                    self.logger.error(f"Maximum number of retries reached for {json_rpc_endpoint}")
                    return e

            except Exception as e:
                if attempt < self.max_retries - 1:
                    self.logger.debug(f"{e} occurred during the API request {json_rpc_endpoint}. Retrying...")
                else:
                    self.logger.error(f"Maximum number of retries reached for {json_rpc_endpoint}")
                    return e

            time.sleep(1)  # don't spam the clients.


class BeaconAPIRequest(ClientInstanceRequest):
    def __init__(self, payload: str, max_retries: int = 3, timeout: int = 5):
        super().__init__(payload, max_retries, timeout)

    def perform_request(self, instance: ClientInstance) -> Union[Exception, requests.Response]:
        """
        Perform a request to the beacon client. Either return an exception or a response.
        @param instance: client instance to send the request to.
        @return: response on success, exception otherwise.
        """
        beacon_api_endpoint = instance.get_consensus_beacon_api_path()
        request_str = f"{beacon_api_endpoint}{self.payload}"
        for attempt in range(self.max_retries):
            try:
                response = requests.get(request_str, timeout=self.timeout)
                response.raise_for_status()  # raise an exception based on the response.

                return response

            except (requests.exceptions.RequestException, HTTPError) as e:
                if attempt < self.max_retries - 1:
                    self.logger.debug(
                        f"{e.strerror} occurred during the API request {beacon_api_endpoint}. Retrying...")
                else:
                    self.logger.error(f"Maximum number of retries reached for {beacon_api_endpoint}")
                    return e

            except Exception as e:
                if attempt < self.max_retries - 1:
                    self.logger.debug(f"{e} occurred during the API request {beacon_api_endpoint}. Retrying...")
                else:
                    self.logger.error(f"Maximum number of retries reached for {beacon_api_endpoint}")
                    return e

            time.sleep(1)  # don't spam the clients.


def perform_batched_request(req: ClientInstanceRequest, clients: list[ClientInstance]) -> dict[ClientInstance, Future]:
    """
    Performs a batched request on a list of clients asynchronously. It returns a dictionary
    of futures, keyed by the client instance name.
    @param req:
    @param clients:
    @return: the future from req.perform_request(client_instance)
    """
    with ThreadPoolExecutor(max_workers=len(clients)) as executor:
        results_dict: dict[ClientInstance, Future] = {}
        for client in clients:
            results_dict[client] = executor.submit(req.perform_request, client)

    return results_dict

"""
    Some predefined useful JSON-RPC requests for EL
"""


class eth_getBlockByNumber(ExecutionJSONRPCRequest):
    def __init__(self, block="latest", _id: int = 1, max_retries: int = 3, timeout: int = 5):
        payload = {
            "method": "eth_getBlockByNumber",
            "params": [block, True],
            "jsonrpc": "2.0",
            "id": _id,
        }
        super().__init__(
            payload=payload,
            max_retries=max_retries,
            timeout=timeout,
        )

    def get_block(self, response):
        """
        Get the block from the response, if it is valid. Returns exception otherwise.
        @param response:
        @return:
        """
        if self.is_valid(response):
            return response.json()["result"]
        else:
            return response


class admin_nodeInfo(ExecutionJSONRPCRequest):
    def __init__(self, _id: int = 1, max_retries: int = 3, timeout: int = 5):
        payload = {
            "method": "admin_nodeInfo",
            "params": [],
            "jsonrpc": "2.0",
            "id": _id,
        }
        super().__init__(
            payload=payload,
            max_retries=max_retries,
            timeout=timeout,
        )

    def get_enode(self, response: Union[Exception, requests.Response]) -> Union[Exception, str]:
        """
        Get the enode from the response, if it is valid. Returns exception otherwise.
        @param response: the response from performing this query.
        @return:
        """
        if self.is_valid(response):
            return response.json()["result"]["enode"]
        else:
            return response  # the exception


class admin_addPeer(ExecutionJSONRPCRequest):
    """
        Add a peer to the node.
        enode: The enode of the peer to add.
    """

    def __init__(
            self, enode: str, _id: int = 1, max_retries: int = 3, timeout: int = 5
    ):
        payload = {
            "method": "admin_addPeer",
            "params": [enode],
            "jsonrpc": "2.0",
            "id": _id,
        }
        super().__init__(
            payload=payload,
            max_retries=max_retries,
            timeout=timeout,
        )


"""
    Some useful predefined BeaconAPI requests for CL
"""


class beacon_getBlockV2(BeaconAPIRequest):
    # https://ethereum.github.io/beacon-APIs/#/Beacon/getBlockV2
    def __init__(self, block="head", max_retries: int = 3, timeout: int = 5):
        payload = f"/eth/v2/beacon/blocks/{block}"
        super().__init__(
            payload=payload,
            max_retries=max_retries,
            timeout=timeout
        )

    def get_block(self, response: Union[Exception, requests.Response]) -> Union[Exception, dict]:
        if self.is_valid(response):
            return response.json()["data"]["message"]
        else:
            return response  # the exception


class beacon_getGenesis(BeaconAPIRequest):
    # https://ethereum.github.io/beacon-APIs/#/Beacon/getGenesis
    def __init__(self, max_retries: int = 3, timeout: int = 5):
        payload = f"/eth/v1/beacon/genesis"
        super().__init__(
            payload,
            max_retries=max_retries,
            timeout=timeout,
        )


class beacon_getFinalityCheckpoints(BeaconAPIRequest):
    # https://ethereum.github.io/beacon-APIs/#/Beacon/getStateFinalityCheckpoints
    def __init__(self, state_id="head", max_retries: int = 3, timeout: int = 5):
        payload = f"/eth/v1/beacon/states/{state_id}/finality_checkpoints"
        super().__init__(
            payload=payload,
            max_retries=max_retries,
            timeout=timeout,
        )
