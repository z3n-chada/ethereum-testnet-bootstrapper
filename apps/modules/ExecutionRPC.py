"""
    HTTP/WS API interface for simple tasks.
"""
import requests
import time
from concurrent.futures import ThreadPoolExecutor


def _threadpool_executor_rpc_request_proxy(bucket, execution_json_rpc, rpc):
    return bucket, execution_json_rpc.get_rpc_response(rpc)


class RPCMethod(object):
    """
    A generic method that we can send and receive.
    """

    def __init__(self, method, params, _id=1, timeout=5):
        self.payload = {
            "method": method,
            "params": params,
            "jsonrpc": "2.0",
            "id": _id,
        }
        self.timeout = timeout

    def get_response(self, url):
        start = int(time.time())
        to = self.timeout
        while time.time() - start < to:
            try:
                response = requests.post(url, json=self.payload, timeout=to)
                return response

            except requests.ConnectionError:
                # odds are the bootstrapper is trying to connect to a client
                # that is not up already.
                print(
                    f"{url}: {self.payload}: getting requests.ConnectionError",
                    flush=True,
                )
                # time.sleep(1)  # should we just return None?
                return None
            except requests.Timeout as e:
                # actually timed out.
                raise e


class eth_get_block_RPC(RPCMethod):
    def __init__(self, blk="latest", _id=1, timeout=5):
        super().__init__("eth_getBlockByNumber", [blk, True], _id, timeout)


class admin_node_info_RPC(RPCMethod):
    def __init__(self, _id=1, timeout=5):
        super().__init__("admin_nodeInfo", [], _id, timeout)


class admin_add_peer_RPC(RPCMethod):
    def __init__(self, enode, _id=1, timeout=5):
        super().__init__("admin_addPeer", [enode], _id, timeout)


class admin_peers_RPC(RPCMethod):
    def __init__(self, _id=1, timeout=5):
        super().__init__("admin_peers", [], _id, timeout)


class ExecutionJSONRPC(object):
    """
    A client that represents a single execution endpoint to interact with.
    """

    def __init__(self, endpoint_url, non_error=True, timeout=5, retry_delay=1):
        self.endpoint_url = endpoint_url
        self.non_error = non_error
        self.timeout = timeout
        self.retry_delay = retry_delay

    def _is_valid_response(self, response):
        if self.non_error:
            if response is None:
                return False
            if response.status_code == 200:
                if "error" not in response.json():
                    return True
        else:
            return False

    def get_rpc_response(self, rpc):
        start = int(time.time())
        while int(time.time()) <= start + self.timeout:
            response = rpc.get_response(self.endpoint_url)
            if self._is_valid_response(response):
                return response.json()
            time.sleep(self.retry_delay)
        return response


class ETBExecutionRPC(object):
    """
    Wrapper around the etb-config that allows you to make batch requests or
    requests to one specific client.
    """

    def __init__(
        self, etb_config, non_error=True, timeout=5, retry_delay=1, protocol="http"
    ):
        self.etb_config = etb_config
        self.non_error = non_error
        self.timeout = timeout
        self.retry_delay = retry_delay
        self.protocol = protocol

        if protocol not in ["http", "ws"]:
            err = "non-implemented protocol for ExecutionRPC connection"
            raise Exception(err)

        self._get_all_execution_endpoints()

    def _get_all_execution_endpoints(self):
        self.execution_endpoints = {}
        for name, ec in self.etb_config.get("execution-clients").items():
            for node in range(ec.get("num-nodes")):
                ip = ec.get("ip-addr", node)
                port = ec.get(f"execution-{self.protocol}-port")
                url = f"{self.protocol}://{ip}:{port}"
                self.execution_endpoints[f"{name}-{node}"] = ExecutionJSONRPC(
                    url, self.non_error, self.timeout
                )

        for name, cc in self.etb_config.get("consensus-clients").items():
            if cc.has_local_exectuion_client:
                for node in range(cc.get("num-nodes")):
                    ip = cc.get("ip-addr", node)
                    port = cc.get(f"execution-{self.protocol}-port")
                    url = f"{self.protocol}://{ip}:{port}"
                    _name = f"{name}-{node}"
                    self.execution_endpoints[_name] = ExecutionJSONRPC(
                        url, self.non_error, self.timeout
                    )

    def get_client_nodes(self):
        return self.execution_endpoints.keys()

    def do_rpc_request(
        self, execution_rpc_method, client_nodes=[None], all_clients=False
    ):
        if all_clients:
            ep = self.get_client_nodes()
        else:
            if not isinstance(client_nodes, list):
                ep = [client_nodes]
            else:
                ep = client_nodes

            for cn in ep:
                if cn not in self.execution_endpoints.keys():
                    err = f"Invalid execution endpoint supplied: {cn}"
                    err += f" must be in {self.get_client_nodes()}"
                    raise Exception(err)

        all_responses = {}
        threadpool_endpoints = [self.execution_endpoints[name] for name in ep]
        threadpool_buckets = [name for name in ep]

        with ThreadPoolExecutor(max_workers=len(ep)) as executor:
            results = executor.map(
                _threadpool_executor_rpc_request_proxy,
                threadpool_buckets,
                threadpool_endpoints,
                [execution_rpc_method for x in range(len(ep))],
            )

            for bucket_response_tuple in list(results):
                client = bucket_response_tuple[0]
                response = bucket_response_tuple[1]
                all_responses[client] = response

        return all_responses
