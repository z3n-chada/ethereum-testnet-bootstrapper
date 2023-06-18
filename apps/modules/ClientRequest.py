"""
    Interfaces for sending and receiving requests and responses
    from CL and EL clients across the network.
"""
import logging
import time
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Union

import requests
from .ETBConfig import ClientInstance


class RequestType(str, Enum):
    BeaconAPIRequest = "BeaconAPIRequest"
    ExecutionRPCRequest = "ExecutionJSONRPCRequest"


class RequestProtocol(str, Enum):
    HTTP = "http"
    WS = "ws"


class ClientRequestBadStatusCodeException(Exception):
    pass


class ClientRequestBadResponseException(Exception):
    pass


class ClientRequest(object):
    """
    A client request is any message sent to a node that expects a response.
    This can be sent either to the execution client or the consensus client.

    This isn't meant to be used directly, instead use the ExecutionRPCRequest or
    ConsensusBeaconAPIRequest classes.
    """

    def __init__(
            self,
            payload: Union[dict, str],
            req_type: RequestType,
            logger: logging.Logger = None,
            protocol: RequestProtocol = RequestProtocol.HTTP,
            timeout=5,
    ):
        self.payload: Union[dict, str] = payload
        self.timeout: int = timeout
        self.req_type: RequestType = req_type
        self.req_protocol: RequestProtocol = protocol
        self.response: requests.Response = requests.Response()
        self.valid_response: bool = False
        self.last_seen_exception: Union[Exception, None] = None

        if logger is None:
            self.logger = logging.getLogger()
        else:
            self.logger = logger

        if self.req_protocol != RequestProtocol.HTTP:
            raise Exception("only http requests have been tested.")

    @abstractmethod
    def perform_request(self, instance: ClientInstance) -> Union[Exception, None]:
        """
            Execution client response status codes behave differently than
            consensus client response status codes, so we overload them.
        """
        pass

    def retrieve_response(self) -> Union[Exception, dict]:
        # can be overwritten for useful parsers on certain messages.
        if self.valid_response:
            if self.req_type == RequestType.BeaconAPIRequest:
                return self.response.json()["data"]
            else:
                return self.response.json()["result"]
        else:
            return ClientRequestBadResponseException()


class ExecutionRPCRequest(ClientRequest):
    """
        An RPC request sent over http/ws to an execution layer client.
    """

    def __init__(self,
                 payload: dict,
                 logger: logging.Logger = None,
                 request_protocol: RequestProtocol = RequestProtocol.HTTP,
                 timeout=5):
        super().__init__(payload,
                         RequestType.ExecutionRPCRequest,
                         logger=logger,
                         protocol=request_protocol,
                         timeout=timeout)

    def perform_request(self, instance: ClientInstance) -> Union[Exception, None]:
        """
            Perform the request on the client, returns an exception if there is one.
            Includes nasty workaround for clients that return 200 status-codes on errors.
            (looking at you besu)
        """
        start = int(time.time())
        end = start + self.timeout
        path = self.payload["method"]
        request_repr = instance.get_execution_jsonrpc_path()

        while int(time.time()) <= end:
            try:
                self.response = requests.post(request_repr, json=self.payload, timeout=self.timeout)
                if self.response.status_code == 200:
                    # besu behaves strangely on startup. 200 type responses can be an error.
                    if "error" in self.response.json():
                        self.last_seen_exception = Exception(self.response.json()["error"])
                        self.logger.error(
                            f"{self.req_type}::{request_repr}{path} returned error: {self.response.json()['error']}"
                        )
                        continue
                    # success
                    self.valid_response = True
                    return None

            except requests.ConnectionError as e:
                self.last_seen_exception = e
                self.logger.error(
                    f"{self.req_type}::{request_repr}{path} ConnectionError Exception, retrying."
                )
            except requests.Timeout as e:
                self.last_seen_exception = e
                self.logger.error(
                    f"{self.req_type}::{request_repr}{path} Timeout Exception"
                )
            except Exception as e:
                self.last_seen_exception = e
                self.logger.error(
                    f"{self.req_type}::{request_repr}{path} Unexpected Exception {e}. Retrying.."
                )

            time.sleep(0.5)  # dont spam

        # if we get here, we either have a 200 that was an error, or a non-200.
        if self.response.status_code == 200:
            # Should never occur, but just in case.
            if "error" not in self.response.json():
                raise Exception("Unexpected error")
            # we got a 200 that was actually an error.
            return self.response.json()["error"]

        return self.last_seen_exception


class ConsensusBeaconAPIRequest(ClientRequest):
    """
        A request sent to a beacon node API endpoint.
    """

    def __init__(self,
                 payload: str,
                 logger: logging.Logger = None,
                 request_protocol: RequestProtocol = RequestProtocol.HTTP,
                 timeout=5):

        super().__init__(payload,
                         RequestType.BeaconAPIRequest,
                         logger=logger,
                         protocol=request_protocol,
                         timeout=timeout)

        self.last_seen_response = None

    def perform_request(self, client: ClientInstance) -> (Exception, requests.Response):
        start = int(time.time())
        end = start + self.timeout
        request_repr = f"{client.get_consensus_beacon_api_path()}{self.payload}"

        while int(time.time()) <= end:
            try:
                self.response = requests.get(request_repr, timeout=self.timeout)
                self.logger.debug(f"{self.req_type}::{request_repr} got status_code: {self.response.status_code}")
                if self.response.status_code == 200:
                    self.valid_response = True
                    return None

            except requests.ConnectionError as e:
                self.last_seen_exception = e
                self.logger.error(
                    f"{self.req_type}::{request_repr} ConnectionError Exception, retrying."
                )
            except requests.Timeout as e:
                self.last_seen_exception = e
                self.logger.error(
                    f"{self.req_type}::{request_repr} Timeout Exception"
                )
            except Exception as e:
                self.last_seen_exception = e
                self.logger.error(
                    f"{self.req_type}::{request_repr} Unexpected Exception {e}. Retrying.."
                )

            time.sleep(0.5)  # dont spam

        return self.last_seen_exception


def perform_request_proxy(job: tuple[ClientRequest, ClientInstance]):
    """
        A proxy function for the ThreadPoolExecutor to use, yields the request
        object instead of the result of perform_request.
    """
    req = job[0]
    req.perform_request(job[1])
    return req


def perform_batched_request(req: ClientRequest, clients: list[ClientInstance]):
    """
        Perform a request on a list of clients asynchronously, returns a list
        of tuples of (client, request)
    @param req: ClientRequest The request to perform
    @param clients: list[ClientInstance) of client instances.
    @return:
    """
    request_iter = [req for x in range(len(clients))]
    with ThreadPoolExecutor(max_workers=len(clients)) as executor:
        results = executor.map(perform_request_proxy, zip(request_iter, clients))
    return zip(clients, results)


"""
    Some predefined useful JSON-RPC requests for EL
"""


class eth_getBlockByNumber(ExecutionRPCRequest):
    def __init__(
            self, block="latest", logger: logging.Logger = None, _id: int = 1, timeout=5
    ):
        payload = {
            "method": "eth_getBlockByNumber",
            "params": [block, True],
            "jsonrpc": "2.0",
            "id": _id,
        }
        super().__init__(
            payload,
            logger=logger,
            request_protocol=RequestProtocol.HTTP,
            timeout=timeout,
        )


class admin_nodeInfo(ExecutionRPCRequest):
    def __init__(self, logger: logging.Logger = None, _id: int = 1, timeout=5):
        payload = {
            "method": "admin_nodeInfo",
            "params": [],
            "jsonrpc": "2.0",
            "id": _id,
        }
        super().__init__(
            payload,
            logger=logger,
            request_protocol=RequestProtocol.HTTP,
            timeout=timeout,
        )

    def get_enode(self):
        if self.valid_response:
            return self.response.json()["result"]["enode"]


class admin_addPeer(ExecutionRPCRequest):
    """
        Add a peer to the node.
        enode: The enode of the peer to add.
    """

    def __init__(
            self, enode: str, logger: logging.Logger = None, _id: int = 1, timeout=5
    ):
        payload = {
            "method": "admin_addPeer",
            "params": [enode],
            "jsonrpc": "2.0",
            "id": _id,
        }
        super().__init__(
            payload,
            logger=logger,
            request_protocol=RequestProtocol.HTTP,
            timeout=timeout,
        )


"""
    Some useful predefined BeaconAPI requests for CL
"""


class beacon_getBlockV2(ConsensusBeaconAPIRequest):
    # https://ethereum.github.io/beacon-APIs/#/Beacon/getBlockV2
    def __init__(self, block="head", logger: logging.Logger = None, timeout: int = 5):
        payload = f"/eth/v2/beacon/blocks/{block}"
        super().__init__(
            payload,
            logger=logger,
            request_protocol=RequestProtocol.HTTP,
            timeout=timeout
        )

    def retrieve_response(self) -> Union[Exception, dict]:
        if self.valid_response:
            return self.response.json()["data"]["message"]
        else:
            return ClientRequestBadResponseException()


class beacon_getGenesis(ConsensusBeaconAPIRequest):
    # https://ethereum.github.io/beacon-APIs/#/Beacon/getGenesis
    def __init__(self, logger: logging.Logger = None, timeout: int = 5):
        payload = f"/eth/v1/beacon/genesis"
        super().__init__(
            payload,
            logger=logger,
            request_protocol=RequestProtocol.HTTP,
            timeout=timeout
        )


class beacon_getFinalityCheckpoints(ConsensusBeaconAPIRequest):
    # https://ethereum.github.io/beacon-APIs/#/Beacon/getStateFinalityCheckpoints
    def __init__(self, state_id="head", logger: logging.Logger = None, timeout: int = 5):
        payload = f"/eth/v1/beacon/states/{state_id}/finality_checkpoints"
        super().__init__(
            payload,
            logger=logger,
            request_protocol=RequestProtocol.HTTP,
            timeout=timeout
        )
