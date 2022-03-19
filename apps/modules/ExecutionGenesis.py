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

        config = {
            "chainId": self.ec["chain-id"],
            "homesteadBlock": 0,
            "eip150Block": 0,
            "eip155Block": 0,
            "eip158Block": 0,
            "byzantiumBlock": 0,
            "constantinopleBlock": 0,
            "petersburgBlock": 0,
            "istanbulBlock": 0,
            "berlinBlock": 0,
            "londonBlock": 0,
            "mergeForkBlock": self.ec["merge-fork-block"],
            "terminalTotalDifficulty": self.ec["terminal-total-difficulty"],
        }
        self.genesis["config"] = config

        if "clique" in self.ec:
            if self.ec["clique"]["enabled"]:
                signers = "".join(s for s in self.ec["clique"]["signers"])
                extradata = f"0x{'0'*64}{signers}{'0'*130}"
                self.genesis["extraData"] = extradata
                self.genesis["config"]["clique"] = {
                    "period": self.ec["seconds-per-eth1-block"],
                    "epoch": self.ec["clique"]["epoch"],
                }
        return self.genesis

    def create_besu_genesis(self):
        # "baseFeePerGas": self.ec["base-fee-per-gas"],
        self.genesis = {
            "alloc": self.get_allocs(),
            "coinbase": "0x0000000000000000000000000000000000000000",
            "difficulty": "0x01",
            "extraData": "",
            "gasLimit": "0x400000",
            "nonce": "0x1234",
            "mixhash": "0x0000000000000000000000000000000000000000000000000000000000000000",
            "parentHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
            "timestamp": str(self.now),
        }
        config = {
            "chainId": self.ec["chain-id"],
            "homesteadBlock": 0,
            "eip150Block": 0,
            "eip155Block": 0,
            "eip158Block": 0,
            "byzantiumBlock": 0,
            "constantinopleBlock": 0,
            "petersburgBlock": 0,
            "istanbulBlock": 0,
            "berlinBlock": 0,
            "londonBlock": 0,
            "preMergeForkBlock": self.ec["merge-fork-block"],
            "terminalTotalDifficulty": self.ec["terminal-total-difficulty"],
        }
        self.genesis["config"] = config

        if "clique" in self.ec:
            if self.ec["clique"]["enabled"]:
                clique = {}
                params = {
                    "blockperiodseconds": self.ec["seconds-per-eth1-block"],
                    "epochlength": self.ec["clique"]["epoch"],
                }
                clique["params"] = params
                signers = "".join(s for s in self.ec["clique"]["signers"])
                extradata = f"0x{'0'*64}{signers}{'0'*130}"

                self.genesis["extraData"] = extradata
                self.genesis['config']["clique"] = clique
        else:
            self.genesis["config"]["ethash"] = {}
            raise Exception("not implemented in launchers")

        # besu doesn't use keystores like geth, however you can embed the accounts in the genesis.
        mnemonic = self.gc["accounts"]["eth1-account-mnemonic"]
        password = self.gc["accounts"]["eth1-passphrase"]
        premines = self.gc["accounts"]["eth1-premine"]
        for acc in premines:
            acct = w3.eth.account.from_mnemonic(
                mnemonic, account_path=acc, passphrase=password
            )

            self.genesis["alloc"][acct.address]["privateKey"] = acct.privateKey.hex()[
                2:
            ]

        return self.genesis

