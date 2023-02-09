"""
    Interfaces for sending and receiving requests and responses
    from CL and EL clients across the network.
"""
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Union

import requests
from .ETBConfig import ETBConfig, ClientInstance


class RequestType(str, Enum):
    BeaconAPIRequest = "BeaconAPIRequest"
    ExecutionRPCRequest = "ExecutionJSONRPCRequest"


class RequestProtocol(str, Enum):
    HTTP = "http"
    WS = "ws"


class ClientRequestBadStatusCodeException(Exception):
    pass


class ClientRequest(object):
    """
    A client request is any message sent to a node that expects a response.
    """

    def __init__(
        self,
        payload: Union[dict, str],
        req_type: RequestType,
        logger: logging.Logger = None,
        protocol: RequestProtocol = RequestProtocol.HTTP,
        timeout=5,
    ):

        self.payload: dict = payload
        self.timeout: int = timeout
        self.req_type: RequestType = req_type
        self.req_protocol: RequestProtocol = protocol
        self.response: requests.Response = (
            requests.Response()
        )  # currently supports http only.
        self.response.status_code = (
            -1
        )  # set a non-200 status code for downstream exception handling.
        if logger is None:
            self.logger = logging.getLogger()
        else:
            self.logger = logger

        if self.req_protocol != RequestProtocol.HTTP:
            raise Exception("only http requests have been tested.")

    def perform_request(self, client: ClientInstance) -> (Exception, requests.Response):
        """
        Perform the request on the client.
        :param client: client to do the request on
        :return: (True: no exception/False exception, the exception, and the response)
        """
        start = int(time.time())
        end = start + self.timeout
        last_known_err = Exception("No error")

        if self.req_type == RequestType.BeaconAPIRequest:
            base_url = client.get_full_beacon_api_path()
            path = self.payload
        else:
            # just do http
            base_url = client.get_full_execution_http_jsonrpc_path()
            path = self.payload["method"]

        while int(time.time()) <= end:
            try:
                if self.req_type == RequestType.ExecutionRPCRequest:
                    self.response = requests.post(
                        base_url, json=self.payload, timeout=self.timeout
                    )
                else:
                    self.response = requests.get(
                        f"{base_url}{self.payload}", timeout=self.timeout
                    )

                if self.response.status_code == 200:
                    # work around for besu p2p not coming up in time.
                    if (
                        self.req_type == RequestType.ExecutionRPCRequest
                        and self.payload["method"] == "admin_nodeInfo"
                    ):
                        if "error" in self.response.json():
                            self.logger.error(
                                f"{self.req_type}::{base_url}{path} returned error: {self.response.json()['error']}"
                            )
                            continue
                    return None, self.response

            except requests.ConnectionError as e:
                last_known_err = e
                self.logger.error(
                    f"{self.req_type}::{base_url}{path} ConnectionError Exception, retrying."
                )
            except requests.Timeout as e:
                last_known_err = e
                self.logger.error(
                    f"{self.req_type}::{base_url}{path} Timeout Exception"
                )
            except Exception as e:
                last_known_err = e
                self.logger.error(
                    f"{self.req_type}::{base_url}{path} Unexpected Exception {e}. Retrying.."
                )

            time.sleep(0.5)  # dont spam

        if self.response.status_code == 200:
            # unlikely racy condition
            return None, self.response
        elif self.response.status_code == -1:
            return last_known_err, self.response
        else:
            e = ClientRequestBadStatusCodeException(
                f"{self.req_type}::{base_url}{path} returned status code: {self.response.status_code}"
            )
            return e, self.response

    def retrieve_response(self, resp: requests.Response):
        # can be overwritten for useful parsers on certain messages.
        if self.req_type == RequestType.BeaconAPIRequest:
            return resp.json()["data"]
        else:
            return resp.json()["result"]


def perform_batched_request(req: ClientRequest, clients: list[ClientInstance]):
    with ThreadPoolExecutor(max_workers=len(clients)) as executor:
        results = executor.map(req.perform_request, clients)
    return zip(clients, results)


"""
    Some predefined useful JSON-RPC requests for EL
"""


class eth_getBlockByNumber(ClientRequest):
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
            RequestType.ExecutionRPCRequest,
            logger,
            RequestProtocol.HTTP,
            timeout,
        )


class admin_nodeInfo(ClientRequest):
    def __init__(self, logger: logging.Logger = None, _id: int = 1, timeout=5):
        payload = {
            "method": "admin_nodeInfo",
            "params": [],
            "jsonrpc": "2.0",
            "id": _id,
        }
        super().__init__(
            payload,
            RequestType.ExecutionRPCRequest,
            logger,
            RequestProtocol.HTTP,
            timeout,
        )

    def retrieve_response(self, resp: requests.Response):
        self.logger.debug(f"admin_nodeInfo response: {resp.json()}")
        return resp.json()["result"]


class admin_addPeer(ClientRequest):
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
            RequestType.ExecutionRPCRequest,
            logger,
            RequestProtocol.HTTP,
            timeout,
        )

    def retrieve_response(self, resp: requests.Response):
        return resp.json()["result"]


"""
    Some useful predefined BeaconAPI requests for CL
"""


class beacon_getBlockV2(ClientRequest):
    # https://ethereum.github.io/beacon-APIs/#/Beacon/getBlockV2
    def __init__(self, block="head", logger: logging.Logger = None, timeout: int = 5):
        payload = f"/eth/v2/beacon/blocks/{block}"
        super().__init__(
            payload, RequestType.BeaconAPIRequest, logger, RequestProtocol.HTTP, timeout
        )

    def retrieve_response(self, resp: requests.Response):
        return resp.json()["data"]["message"]


class beacon_getGenesis(ClientRequest):
    # https://ethereum.github.io/beacon-APIs/#/Beacon/getGenesis
    def __init__(self, logger: logging.Logger = None, timeout: int = 5):
        payload = f"/eth/v1/beacon/genesis"
        super().__init__(
            payload, RequestType.BeaconAPIRequest, logger, RequestProtocol.HTTP, timeout
        )

    def retrieve_response(self, resp: requests.Response):
        return resp.json()["data"]
