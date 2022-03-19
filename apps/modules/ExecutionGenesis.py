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
                clique = {
                    "blockPeriodSeconds": self.ec["seconds-per-eth1-block"],
                    "epochLength": self.ec["clique"]["epoch"],
                }
                signers = "".join(s for s in self.ec["clique"]["signers"])
                extradata = f"0x{'0'*64}{signers}{'0'*130}"

                self.genesis["extraData"] = extradata
                self.genesis["config"]["clique"] = clique
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
                "networkID": hex(int(self.ec["chain-id"])),
                "MergeForkIdTransition": hex(int(self.ec["merge-fork-block"])),
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
                "timestamp": hex(self.now),
                "parentHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
                "extraData": "",
                "gasLimit": "0x400000",
            },
            "accounts": self.get_allocs(),
            "nodes": [],
        }

        if "clique" in self.ec:
            if self.ec["clique"]["enabled"]:
                self.genesis["engine"]["clique"] = {
                    "params": {
                        "period": hex(self.ec["seconds-per-eth1-block"]),
                        "epoch": hex(self.ec["clique"]["epoch"]),
                    }
                }
                signers = "".join(s for s in self.ec["clique"]["signers"])
                extradata = f"0x{'0'*64}{signers}{'0'*130}"
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

        return self.genesis
