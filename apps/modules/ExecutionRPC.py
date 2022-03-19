"""
    HTTP/WS API interface for simple tasks.
"""
import requests
import json
import time


class RPCMethod(object):
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
        while time.time() - start < self.timeout:
            try:
                response = requests.post(
                    url, json=self.payload, timeout=self.timeout
                ).json()
                if "error" not in response:
                    return response["result"]
                else:
                    return response

            except requests.ConnectionError:
                # odds are the bootstrapper is trying to connect to a client
                # that is not up already.
                pass
            except requests.Timeout as e:
                # actually timed out.
                raise e


class ExecutionClientJsonRPC(object):
    def __init__(self, host, port, timeout=5):
        self.url = f"http://{host}:{port}"
        self.timeout = timeout

    def eth_get_block(self, blk="latest"):
        rpc = RPCMethod(
            "eth_getBlockByNumber", [blk, True], _id=1, timeout=self.timeout
        )
        return rpc.get_response(self.url)

    def admin_node_info(self):
        rpc = RPCMethod("admin_nodeInfo", [], _id=1, timeout=self.timeout)
        return rpc.get_response(self.url)

    def admin_add_peer(self, enode):
        rpc = RPCMethod("admin_addPeer", [enode], _id=1, timeout=self.timeout)
        return rpc.get_response(self.url)

    def admin_peers(self):
        rpc = RPCMethod("admin_peers", [], _id=1, timeout=self.timeout)
        return rpc.get_response(self.url)


if __name__ == "__main__":
    besu_node = "http://10.0.20.2:8645"
    ecjrpc = ExecutionClientJsonRPC("10.0.20.2", 8645)
    print(ecjrpc.eth_get_block())
    print(ecjrpc.admin_node_info())
    print(ecjrpc.admin_peers())
