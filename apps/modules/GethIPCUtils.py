"""
    This module exists to allow a user to interact with a geth ipc session
    to get some useful information to use in other modules.
"""

import pathlib
import time

from web3 import IPCProvider, Web3
from web3.middleware import geth_poa_middleware


class GethIPC(object):
    def __init__(self, ipc_path, timeout=5):
        self.ipc = self._get_ipc_with_timeout(ipc_path, timeout)
        self.ipc.middleware_onion.inject(geth_poa_middleware, layer=0)

    def _get_ipc_with_timeout(self, ipc_path, timeout):
        p_ipc = pathlib.Path(ipc_path)
        max_time = int(time.time()) + timeout
        while int(time.time()) <= max_time:
            if p_ipc.exists():
                return Web3(IPCProvider(ipc_path))
                # connect to ipc
            time.sleep(1)
        raise Exception(f"IPC timeout for: {ipc_path}")

    def get_block(self, blk="latest"):
        return self.ipc.eth.get_block(blk)

    def get_block_hash(self, blk="latest"):
        return self.get_block(blk)["hash"]


if __name__ == "__main__":
    ipc_path = "data/local_testnet/geth/geth.ipc"
    g = GethIPC(ipc_path)
    print(g.get_block())
    print(g.get_block_hash().hex())
