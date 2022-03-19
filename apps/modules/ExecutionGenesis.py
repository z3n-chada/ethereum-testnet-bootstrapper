from web3.auto import w3
from .EthDepositContract import deposit_contract_json

w3.eth.account.enable_unaudited_hdwallet_features()


class ExecutionGenesisWriter(object):
    def __init__(self, global_config):
        self.gc = global_config
        self.genesis = {}
        self.ec = self.gc["config-params"]["execution-layer"]
        self.now = (
            self.gc["now"]
            + self.gc["config-params"]["execution-layer"]["genesis-delay"]
        )

    def get_allocs(self):
        allocs = {}
        # premine allocations
        for x in range(256):
            allocs["0x" + x.to_bytes(length=20, byteorder="big").hex()] = {
                "balance": "1",
            }

        # account allocations
        mnemonic = self.gc["accounts"]["eth1-account-mnemonic"]
        password = self.gc["accounts"]["eth1-passphrase"]
        premines = self.gc["accounts"]["eth1-premine"]
        for acc in premines:
            acct = w3.eth.account.from_mnemonic(
                mnemonic, account_path=acc, passphrase=password
            )
            allocs[acct.address] = {"balance": premines[acc] + "0" * 18}
            # genesis["alloc"][acct.address] = {"balance": premines[acc] + "0" * 18}

        # deposit contract
        allocs[
            self.gc["config-params"]["deposit-contract-address"]
        ] = deposit_contract_json

        return allocs

    def create_geth_genesis(self):

        self.genesis = {
            "alloc": self.get_allocs(),
            "coinbase": "0x0000000000000000000000000000000000000000",
            "difficulty": "0x01",
            "extraData": "",
            "gasLimit": "0x400000",
            "nonce": "0x1234",
            "mixhash": "0x" + ("0" * 64),
            "parentHash": "0x" + ("0" * 64),
            "timestamp": str(self.now),
        }

        config = {}
        config["chainId"] = self.ec["chain-id"]
        config["homesteadBlock"] = 0
        config["eip150Block"] = 0
        config["eip155Block"] = 0
        config["eip158Block"] = 0
        config["byzantiumBlock"] = 0
        config["constantinopleBlock"] = 0
        config["petersburgBlock"] = 0
        config["istanbulBlock"] = 0
        config["berlinBlock"] = 0
        config["londonBlock"] = 0
        config["mergeForkBlock"] = self.ec["merge-fork-block"]
        config["terminalTotalDifficulty"] = self.ec["terminal-total-difficulty"]
        self.genesis["config"] = config

        if "clique" in self.ec:
            if self.ec["clique"]["enabled"]:
                signer = self.ec["clique"]["signer"]
                extradata = f"0x{'00'*32}{signer}{'00'*65}"
                self.genesis["extraData"] = extradata
                self.genesis["config"]["clique"] = {
                    "period": self.ec["seconds-per-eth1-block"],
                    "epoch": self.ec["clique"]["epoch"],
                }
        return self.genesis
