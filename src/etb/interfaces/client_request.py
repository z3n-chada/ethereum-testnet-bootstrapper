"""Interfaces for sending and receiving requests and responses from CL and EL
clients across the network."""

import logging
import time
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor, Future
from enum import Enum
from typing import Union, Tuple

import requests
from requests import HTTPError

from ..config.etb_config import ClientInstance


class RequestType(str, Enum):
    BeaconAPIRequest = "BeaconAPIRequest"
    ExecutionRPCRequest = "ExecutionJSONRPCRequest"


class RequestProtocol(str, Enum):
    HTTP = "http"
    WS = "ws"


class ErrorResponse(Exception):
    """Some clients return 200 status code despite an error."""


class ClientInstanceRequest:
    """A client request is any message sent to a node that expects a response.

    This can be either JSONRPC for ELs, or BeaconAPI for CLs.
    """

    def __init__(
        self, payload: Union[dict, str], max_retries: int = 3, timeout: int = 5
    ):
        """A request to a client instance.

        @param payload: the payload, a dictionary for JSONRPC, a string
        for BeaconAPI. @param max_retries: max number of retries before
        bailing. @param timeout: timeout to use per request.
        """
        self.payload: Union[dict, str] = payload
        self.max_retries: int = max_retries
        self.timeout: int = timeout

    @abstractmethod
    def perform_request(
        self, instance: ClientInstance
    ) -> Union[Exception, requests.Response]:
        """Either returns the response or an exception."""

    def is_valid(self, response: Union[requests.Response, Exception]) -> bool:
        """Check if the response is valid.

        @param response: the response/exception returned from
        perform_request. @return:
        """
        return not isinstance(response, Exception)


class ExecutionJSONRPCRequest(ClientInstanceRequest):
    """A request to an execution client."""

    def __init__(self, payload: dict, max_retries: int = 3, timeout: int = 5):
        super().__init__(payload=payload, max_retries=max_retries, timeout=timeout)

    def perform_request(
        self, instance: ClientInstance
    ) -> Union[Exception, requests.Response]:
        """Perform a request to the execution client. Either return an
        exception or a response. In the case that the response is an error code
        we also return an exception. (besu.

        workaround) @param instance: client instance to send the request
        to. @return: response on success, exception otherwise.
        """
        rpc_endpoint = instance.get_execution_jsonrpc_path()
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    rpc_endpoint, json=self.payload, timeout=self.timeout
                )
                # raise an exception based on the response.
                response.raise_for_status()
                data = response.json()
                if "error" in data:
                    raise ErrorResponse(data["error"])
                # response is good, optionally process data here.
                return response

            except (requests.exceptions.RequestException, HTTPError) as e:
                if attempt < self.max_retries - 1:
                    logging.debug(
                        f"{e.strerror} occurred during the API request {rpc_endpoint}. Retrying..."
                    )
                else:
                    logging.error(
                        f"Maximum number of retries reached for {rpc_endpoint}"
                    )
                    return e

            except Exception as e:
                if attempt < self.max_retries - 1:
                    logging.debug(
                        f"{e} occurred during the API request {rpc_endpoint}. Retrying..."
                    )
                else:
                    logging.error(
                        f"Maximum number of retries reached for {rpc_endpoint}"
                    )
                    return e

            time.sleep(1)  # don't spam the clients.
        return Exception("Unknown error occurred.")  # should not occur.


class BeaconAPIRequest(ClientInstanceRequest):
    def __init__(self, payload: str, max_retries: int = 3, timeout: int = 5):
        super().__init__(payload, max_retries, timeout)

    def perform_request(
        self, instance: ClientInstance
    ) -> Union[Exception, requests.Response]:
        """Perform a request to the beacon client. Either return an exception
        or a response.

        @param instance: client instance to send the request to.
        @return: response on success, exception otherwise.
        """
        beacon_api_endpoint = instance.get_consensus_beacon_api_path()
        request_str = f"{beacon_api_endpoint}{self.payload}"
        for attempt in range(self.max_retries):
            try:
                response = requests.get(request_str, timeout=self.timeout)
                # raise an exception based on the response.
                response.raise_for_status()

                return response

            except (
                requests.exceptions.RequestException,
                HTTPError,
            ) as connection_exception:
                if attempt < self.max_retries - 1:
                    err = connection_exception.strerror
                    logging.debug(
                        f"{err} occurred during the API request {request_str}. Retrying..."
                    )
                else:
                    logging.error(
                        f"Maximum number of retries reached for {request_str}"
                    )
                    return connection_exception

            except Exception as unexpected_exception:
                if attempt < self.max_retries - 1:
                    err = unexpected_exception
                    logging.debug(
                        f"{err} occurred during the API request {request_str}. Retrying..."
                    )
                else:
                    logging.error(
                        f"Maximum number of retries reached for {request_str}"
                    )
                    return unexpected_exception

            time.sleep(1)  # don't spam the clients.


def perform_batched_request(
    req: ClientInstanceRequest, clients: list[ClientInstance]
) -> dict[ClientInstance, Future]:
    """Performs a batched request on a list of clients asynchronously. It
    returns a dictionary.

    of futures, keyed by the client instance name. @param req: @param
    clients: @return: the future from
    req.perform_request(client_instance)
    """
    with ThreadPoolExecutor(max_workers=len(clients)) as executor:
        results_dict: dict[ClientInstance, Future] = {}
        for client in clients:
            results_dict[client] = executor.submit(req.perform_request, client)

    return results_dict


class eth_getBlockByNumber(ExecutionJSONRPCRequest):
    """
    eth_getBlockByNumber jsonRPCRequest
    """

    def __init__(
        self, block="latest", _id: int = 1, max_retries: int = 3, timeout: int = 5
    ):
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
        """Get the block from the response, if it is valid. Returns exception
        otherwise.

        @param response: @return:
        """
        if self.is_valid(response):
            return response.json()["result"]
        else:
            return response


class admin_nodeInfo(ExecutionJSONRPCRequest):
    """
    admin_nodeInfo jsonRPCRequest
    """

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

    def get_enode(
        self, response: Union[Exception, requests.Response]
    ) -> Union[Exception, str]:
        """Get the enode from the response, if it is valid. Returns exception
        otherwise.

        @param response: the response from performing this query.
        @return:
        """
        if self.is_valid(response):
            return response.json()["result"]["enode"]
        return response  # the exception


class admin_addPeer(ExecutionJSONRPCRequest):
    """
    admin_addPeer jsonRPCRequest
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


class BeaconAPIgetBlockV2(BeaconAPIRequest):
    """
    /eth/v2/beacon/blocks/{block} beaconAPI request.
    https://ethereum.github.io/beacon-APIs/#/Beacon/getBlockV2
    """

    def __init__(self, block="head", max_retries: int = 3, timeout: int = 5):
        payload = f"/eth/v2/beacon/blocks/{block}"
        super().__init__(payload=payload, max_retries=max_retries, timeout=timeout)

    def get_block(
        self, response: Union[Exception, requests.Response]
    ) -> Union[Exception, dict]:
        if self.is_valid(response):
            return response.json()["data"]["message"]

        return response  # the exception


class BeaconAPIgetGenesis(BeaconAPIRequest):
    """
    /eth/v1/beacon/genesis beaconAPI request.
    https://ethereum.github.io/beacon-APIs/#/Beacon/getGenesis
    """

    def __init__(self, max_retries: int = 3, timeout: int = 5):
        payload = f"/eth/v1/beacon/genesis"
        super().__init__(
            payload,
            max_retries=max_retries,
            timeout=timeout,
        )


class BeaconAPIgetFinalityCheckpoints(BeaconAPIRequest):
    """
    /eth/v1/beacon/states/{state_id}/finality_checkpoints beaconAPI request.
    https://ethereum.github.io/beacon-APIs/#/Beacon/getStateFinalityCheckpoints
    """

    def __init__(self, state_id="head", max_retries: int = 3, timeout: int = 5):
        payload = f"/eth/v1/beacon/states/{state_id}/finality_checkpoints"
        super().__init__(
            payload=payload,
            max_retries=max_retries,
            timeout=timeout,
        )

    def get_finalized_checkpoint(
        self, response: Union[Exception, requests.Response]
    ) -> Union[Exception, Tuple[int, str]]:
        """Get the finalized checkpoint from the response, if it is valid.
        Returns exception otherwise.

        @param response: the response from performing this query.
        @return
        : (epoch: int, root:str)
        """
        if self.is_valid(response):
            return (
                response.json()["data"]["finalized"]["epoch"],
                response.json()["data"]["finalized"]["root"],
            )

        return response  # the exception

    def get_previous_justified_checkpoint(
        self, response: Union[Exception, requests.Response]
    ) -> Union[Exception, Tuple[int, str]]:
        """Get the previous justified checkpoint from the response, if it is
        valid. Returns exception otherwise.

        @param response: the response from performing this query.
        @return
        : (epoch: int, root:str)
        """
        if self.is_valid(response):
            return (
                response.json()["data"]["previous_justified"]["epoch"],
                response.json()["data"]["previous_justified"]["root"],
            )

        return response  # the exception

    def get_current_justified_checkpoint(
        self, response: Union[Exception, requests.Response]
    ) -> Union[Exception, Tuple[int, str]]:
        """Get the current justified checkpoint from the response, if it is
        valid. Returns exception otherwise.

        @param response: the response from performing this query.
        @return
        : (epoch: int, root:str)
        """
        if self.is_valid(response):
            return (
                response.json()["data"]["current_justified"]["epoch"],
                response.json()["data"]["current_justified"]["root"],
            )

        return response  # the exception


class BeaconAPIgetIdentity(BeaconAPIRequest):
    """
    /eth/v1/beacon/identity beaconAPI request.
    """

    def __init__(self, max_retries: int = 3, timeout: int = 5):
        payload = f"/eth/v1/node/identity"
        super().__init__(
            payload=payload,
            max_retries=max_retries,
            timeout=timeout,
        )

    def get_identity(
        self, response: Union[Exception, requests.Response]
    ) -> Union[Exception, dict]:
        """Get the identity from the response, if it is valid.
        Returns exception otherwise.

        @param response: the response from performing this query.
        @return
        : identity: dict
        """
        if self.is_valid(response):
            return response.json()["data"]

        return response

    def get_enr(
        self, response: Union[Exception, requests.Response]
    ) -> Union[Exception, dict]:
        """Get the ENR from the response, if it is valid.
        Returns exception otherwise.

        @param response: the response from performing this query.
        @return
        : enr: dict
        """
        return self.get_identity(response)["enr"]

    def get_peer_id(
        self, response: Union[Exception, requests.Response]
    ) -> Union[Exception, str]:
        """Get the peer ID from the response, if it is valid.
        Returns exception otherwise.

        @param response: the response from performing this query.
        @return
        : peer_id: str
        """
        return self.get_identity(response)["peer_id"]


class BeaconAPIgetPeers(BeaconAPIRequest):
    """
    /eth/v1/beacon/p2p/peers beaconAPI request.
    https://ethereum.github.io/beacon-APIs/#/Beacon/getPeers
    """

    def __init__(
        self,
        max_retries: int = 3,
        timeout: int = 5,
        directions: list[str] = None,
        states: list[str] = None,
    ):
        payload = f"/eth/v1/node/peers"
        additional_params: bool = False
        state_str = ""
        direction_str = ""
        if states is not None:
            additional_params = True
            for state in states:
                state_str += f"state={state}&"
        if directions is not None:
            additional_params = True
            for direction in directions:
                direction_str += f"direction={direction}&"
        if additional_params:
            payload += f"?{state_str}{direction_str}"
        # remove the trailing &
        payload = payload[:-1]

        super().__init__(
            payload=payload,
            max_retries=max_retries,
            timeout=timeout,
        )

    def get_peers(
        self, response: Union[Exception, requests.Response]
    ) -> Union[Exception, dict]:
        """Get the list of peers from the response, if it is valid. Returns
        exception otherwise.

        @param response: the response from performing this query.
        @return:
        """
        if self.is_valid(response):
            return response.json()["data"]

        return response  # the exception
