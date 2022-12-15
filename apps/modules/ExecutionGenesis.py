from web3.auto import w3

from .EthDepositContract import deposit_contract_json

w3.eth.account.enable_unaudited_hdwallet_features()


class ExecutionGenesisWriter(object):
    def __init__(self, global_config):
        self.etb_config = global_config
        self.genesis = {}
        self.execution_genesis = self.etb_config.get(
            "bootstrap-genesis"
        ) + self.etb_config.get("execution-genesis-delay")

    def get_allocs(self):
        allocs = {}
        # premine allocations
        for x in range(256):
            allocs["0x" + x.to_bytes(length=20, byteorder="big").hex()] = {
                "balance": "1",
            }

        # account allocations
        mnemonic = self.etb_config.get("eth1-account-mnemonic")
        password = self.etb_config.get("eth1-passphrase")
        premines = self.etb_config.get("eth1-premine")
        for acc in premines:
            acct = w3.eth.account.from_mnemonic(
                mnemonic, account_path=acc, passphrase=password
            )
            allocs[acct.address] = {"balance": premines[acc] + "0" * 18}
            # genesis["alloc"][acct.address] = {"balance": premines[acc] + "0" * 18}

        # deposit contract
        allocs[self.etb_config.get("deposit-contract-address")] = deposit_contract_json

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
            "timestamp": str(self.execution_genesis),
        }

        config = {
            "chainId": self.etb_config.get("chain-id"),
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
            "mergeForkBlock": 0,
            "arrowGlacierBlock": 0,
            "grayGlacierBlock": 0,
            "shanghaiTime": self.execution_genesis + self.etb_config.get("shanghai-delay"),
            "terminalTotalDifficulty": 0,
        }
        self.genesis["config"] = config

        return self.genesis

    def create_erigon_genesis(self):

        return self.create_geth_genesis()
        # self.genesis = {
        #     "alloc": self.get_allocs(),
        #     "coinbase": "0x0000000000000000000000000000000000000000",
        #     "difficulty": "0x01",
        #     "extraData": "",
        #     "gasLimit": "0x400000",
        #     "nonce": "0x1234",
        #     "mixhash": "0x" + ("0" * 64),
        #     "parentHash": "0x" + ("0" * 64),
        #     "timestamp": str(self.execution_genesis),
        # }
        #
        # config = {
        #     "chainId": self.etb_config.get("chain-id"),
        #     "homesteadBlock": 0,
        #     "eip150Block": 0,
        #     "eip150Hash": "0x0000000000000000000000000000000000000000000000000000000000000000",
        #     "eip155Block": 0,
        #     "eip158Block": 0,
        #     "byzantiumBlock": 0,
        #     "constantinopleBlock": 0,
        #     "petersburgBlock": 0,
        #     "istanbulBlock": 0,
        #     "berlinBlock": 0,
        #     "londonBlock": 0,
        #     "terminalBlockHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
        #     "mergeNetsplitBlock": self.etb_config.get("merge-fork-block"),
        #     "terminalTotalDifficulty": self.etb_config.get("terminal-total-difficulty"),
        # }
        # self.genesis["config"] = config
        #
        # if self.etb_config.get("clique-enabled"):
        #     signers = "".join(s for s in self.etb_config.get("clique-signers"))
        #     extradata = f"0x{'0' * 64}{signers}{'0' * 130}"
        #     self.genesis["extraData"] = extradata
        #     self.genesis["config"]["clique"] = {
        #         "period": self.etb_config.get("seconds-per-eth1-block"),
        #         "epoch": self.etb_config.get("clique-epoch"),
        #     }
        #     self.genesis["config"]["consensus"] = "clique"
        #
        # return self.genesis

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
            "timestamp": str(self.execution_genesis),
        }
        config = {
            "chainId": self.etb_config.get("chain-id"),
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
            "preMergeForkBlock": self.etb_config.get("merge-fork-block"),
            "terminalTotalDifficulty": self.etb_config.get("terminal-total-difficulty"),
        }
        self.genesis["config"] = config

        if self.etb_config.get("clique-enabled"):
            clique = {
                "blockPeriodSeconds": self.etb_config.get("seconds-per-eth1-block"),
                "epochLength": self.etb_config.get("clique-epoch"),
            }
            signers = "".join(s for s in self.etb_config.get("clique-signers"))
            extradata = f"0x{'0' * 64}{signers}{'0' * 130}"

            self.genesis["extraData"] = extradata
            self.genesis["config"]["clique"] = clique
        else:
            self.genesis["config"]["ethash"] = {}
            raise Exception("not implemented in launchers")

        # besu doesn't use keystores like geth, however you can embed the accounts in the genesis.
        mnemonic = self.etb_config.get("eth1-account-mnemonic")
        password = self.etb_config.get("eth1-passphrase")
        premines = self.etb_config.get("eth1-premine")
        for acc in premines:
            acct = w3.eth.account.from_mnemonic(
                mnemonic, account_path=acc, passphrase=password
            )

            self.genesis["alloc"][acct.address]["privateKey"] = acct.privateKey.hex()[
                                                                2:
                                                                ]
        raise Exception("Reimplement me.")
        return self.genesis

    def create_nethermind_genesis(self):
        self.genesis = {
            "name": "kilnv2",
            "engine": {},
            "params": {
                "gasLimitBoundDivisor": "0x400",
                "registrar": "0x0000000000000000000000000000000000000000",
                "accountStartNonce": "0x0",
                "maximumExtraDataSize": "0xffff",
                "minGasLimit": "0x1388",
                "networkID": hex(int(self.etb_config.get("chain-id"))),
                "MergeForkIdTransition": hex(
                    int(self.etb_config.get("merge-fork-block"))
                ),
                "eip150Transition": "0x0",
                "eip158Transition": "0x0",
                "eip160Transition": "0x0",
                "eip161abcTransition": "0x0",
                "eip161dTransition": "0x0",
                "eip155Transition": "0x0",
                "eip140Transition": "0x0",
                "eip211Transition": "0x0",
                "eip214Transition": "0x0",
                "eip658Transition": "0x0",
                "eip145Transition": "0x0",
                "eip1014Transition": "0x0",
                "eip1052Transition": "0x0",
                "eip1283Transition": "0x0",
                "eip1283DisableTransition": "0x0",
                "eip152Transition": "0x0",
                "eip1108Transition": "0x0",
                "eip1344Transition": "0x0",
                "eip1884Transition": "0x0",
                "eip2028Transition": "0x0",
                "eip2200Transition": "0x0",
                "eip2565Transition": "0x0",
                "eip2929Transition": "0x0",
                "eip2930Transition": "0x0",
                "eip1559Transition": "0x0",
                "eip3198Transition": "0x0",
                "eip3529Transition": "0x0",
                "eip3541Transition": "0x0",
            },
            "genesis": {
                "seal": {
                    "ethereum": {
                        "nonce": "0x1234",
                        "mixHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
                    }
                },
                "difficulty": "0x01",
                "author": "0x0000000000000000000000000000000000000000",
                "timestamp": hex(self.execution_genesis),
                "parentHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
                "extraData": "",
                "gasLimit": "0x400000",
            },
            "accounts": self.get_allocs(),
            "nodes": [],
        }

        if self.etb_config.get("clique-enabled"):
            # self.genesis["engine"]["clique"] = {
            #    "params": {
            #        "period": hex(self.etb_config.get("seconds-per-eth1-block")),
            #        "epoch": hex(self.etb_config.get("clique-epoch")),
            #    }
            # }
            self.genesis["engine"]["clique"] = {
                "params": {
                    "period": self.etb_config.get("seconds-per-eth1-block"),
                    "epoch": self.etb_config.get("clique-epoch"),
                }
            }
            signers = "".join(s for s in self.etb_config.get("clique-signers"))
            extradata = f"0x{'0' * 64}{signers}{'0' * 130}"
            self.genesis["genesis"]["extraData"] = extradata
        else:
            self.genesis["engine"]["Ethash"] = {
                "params": {
                    "minimumDifficulty": "0x20000",
                    "difficultyBoundDivisor": "0x800",
                    "durationLimit": "0xd",
                    "blockReward": {"0x0": "0x1BC16D674EC80000"},
                    "homesteadTransition": "0x0",
                    "eip100bTransition": "0x0",
                    "difficultyBombDelays": {},
                }
            }
            raise Exception("ethash network not implemented")
        raise Exception("Reimplement me.")
        return self.genesis
