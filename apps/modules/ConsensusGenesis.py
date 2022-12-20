"""
    Contains all of the neccessary information and functionality to write the
    consensus config.yaml and genesis.ssz.
"""
import logging
import subprocess

from ruamel import yaml

logger = logging.getLogger("bootstrapper_log")


class ConsensusGenesisWriter(object):
    def __init__(self, etb_config):
        self.etb_config = etb_config

        self.minimal_defaults = {
            "max-committees-per-slot": 4,
            "target-committee-size": 4,
            "shuffle-round-count": 10,
            "eth1-follow-distance": 16,
            "seconds-per-slot": 12,
            "slots-per-epoch": 8,
            "epochs-per-eth1-voting-period": 4,
            "slots-per-historical-root": 64,
            "shard-committee-period": 64,
            "epochs-per-historical-vector": 64,
            "epochs-per-slashings-vector": 64,
            "inactivity-penalty-quotient": 33554432,
            "min-slashing-penalty-quotient": 64,
            "proportional-slashing-multiplier": 2,
            "churn-limit-quotient": 32,
        }

        self.mainnet_defaults = {
            "max-committees-per-slot": 64,
            "target-committee-size": 128,
            "shuffle-round-count": 90,
            "eth1-follow-distance": 2048,
            "seconds-per-slot": 12,
            "slots-per-epoch": 32,
            "epochs-per-eth1-voting-period": 64,
            "slots-per-historical-root": 8192,
            "shard-committee-period": 256,
            "epochs-per-historical-vector": 65536,
            "epochs-per-slashings-vector": 8192,
            "inactivity-penalty-quotient": 67108864,
            "min-slashing-penalty-quotient": 128,
            "proportional-slashing-multiplier": 2,
            "churn-limit-quotient": 65536,
        }

        self.potential_overrides = [
            "eth1-follow-distance",
            "min-genesis-active-validator-count",
        ]

    def create_consensus_genesis(self):
        """
        Create the consensus genesis.ssz file with eth2-testnet-genesis.
        currently we only use post-merge genesis with no withdrawal.
        """
        mnemonic = self.etb_config.get("validator-mnemonic")
        config = self.etb_config.get("consensus-config-file")
        state_out = self.etb_config.get("consensus-genesis-file")
        num_deposits = self.etb_config.get("min-genesis-active-validator-count")
        eth1_config = self.etb_config.get("geth-genesis-file")

        logger.debug("Creating genesis ssz using:")
        logger.debug(f"mnemonic: {mnemonic}")
        logger.debug(f"num_deposits {num_deposits}")
        logger.debug(f"config {config}")
        logger.debug(f"eth1-config {eth1_config}")
        logger.debug(f"ssz path: {state_out}")

        with open("/tmp/validators.yaml", "w") as f:
            yaml.dump(
                [
                    {
                        "mnemonic": mnemonic,
                        "count": num_deposits,
                    }
                ],
                f,
            )

        cmd = [
            "eth2-testnet-genesis",
            "merge",
            "--mnemonics",
            "/tmp/validators.yaml",
            "--config",
            config,
            "--state-output",
            state_out,
            "--eth1-config",
            eth1_config
        ]
        logger.debug(f"ConsensusGenesis: running eth2-testnet-genesis:\n{cmd}")
        subprocess.run(cmd, capture_output=True)

        with open(state_out, "rb") as f:
            ssz = f.read()

        return ssz

    def _get_potential_overrides(self):
        # fetch potential overrides for config-params
        cc = self.etb_config.global_config["config-params"]["consensus-layer"]
        overrides = {}
        for po in self.potential_overrides:
            if po in cc:
                overrides[po] = cc[po]

        return overrides

    def create_consensus_config(self):
        if self.etb_config.get("preset-base") == "minimal":
            # preset defaults
            pd = self.minimal_defaults
        elif self.etb_config.get("preset-base") == "mainnet":
            # preset defaults
            pd = self.mainnet_defaults
        else:
            raise Exception(
                f"Invalid preset base for consensus config: {self.etb_config.get('preset-base')}"
            )

        overrides = self._get_potential_overrides()
        logger.debug(f"ConsensusConfig: using overrides {overrides}")
        for k, v in overrides.items():
            pd[k] = v
        return f"""
PRESET_BASE: \"{self.etb_config.get('preset-base')}\"

# Genesis
# ---------------------------------------------------------------
# [customized]
MIN_GENESIS_ACTIVE_VALIDATOR_COUNT: {self.etb_config.get('min-genesis-active-validator-count')}

MIN_GENESIS_TIME: {self.etb_config.get('bootstrap-genesis')}
GENESIS_FORK_VERSION: 0x{self.etb_config.get('genesis-fork-version'):08x}
GENESIS_DELAY: 0

# Forking
# ---------------------------------------------------------------
# Values provided for illustrative purposes.
# Individual tests/testnets may set different values.

# Altair
ALTAIR_FORK_VERSION: 0x{self.etb_config.get('altair-fork-version'):08x}
ALTAIR_FORK_EPOCH: {self.etb_config.get('altair-fork-epoch')}
# Bellatrix (aka merge)
BELLATRIX_FORK_VERSION: 0x{self.etb_config.get('bellatrix-fork-version'):08x}
BELLATRIX_FORK_EPOCH: {self.etb_config.get('bellatrix-fork-epoch')}
# Sharding
SHARDING_FORK_VERSION: 0x{self.etb_config.get('sharding-fork-version'):08x}
SHARDING_FORK_EPOCH: {self.etb_config.get('sharding-fork-epoch')}

# TBD, 2**32 is a placeholder. Merge transition approach is in active R&D.
MIN_ANCHOR_POW_BLOCK_DIFFICULTY: 4294967296

# Time parameters
# ---------------------------------------------------------------
# [customized] Faster for testing purposes
SECONDS_PER_SLOT: {pd['seconds-per-slot']}
# 14 (estimate from Eth1 mainnet)
SECONDS_PER_ETH1_BLOCK: {self.etb_config.get('seconds-per-eth1-block')}
MIN_VALIDATOR_WITHDRAWABILITY_DELAY: 256
SHARD_COMMITTEE_PERIOD: {pd['shard-committee-period']}
ETH1_FOLLOW_DISTANCE: {pd['eth1-follow-distance']}

# Validator cycle
# ---------------------------------------------------------------
# 2**2 (= 4)
INACTIVITY_SCORE_BIAS: 4
# 2**4 (= 16)
INACTIVITY_SCORE_RECOVERY_RATE: 16
# 2**4 * 10**9 (= 16,000,000,000) Gwei
EJECTION_BALANCE: 16000000000
# 2**2 (= 4)
MIN_PER_EPOCH_CHURN_LIMIT: 4
# [customized] scale queue churn at much lower validator counts for testing
CHURN_LIMIT_QUOTIENT: {pd['churn-limit-quotient']}

# Transition
# ---------------------------------------------------------------
# TBD, 2**256-2**10 is a placeholder
TERMINAL_TOTAL_DIFFICULTY: {self.etb_config.get('terminal-total-difficulty')}
# By default, don't use these params
TERMINAL_BLOCK_HASH: {self.etb_config.get('terminal-block-hash')}
TERMINAL_BLOCK_HASH_ACTIVATION_EPOCH: {self.etb_config.get('terminal-block-hash-activation-epoch')}


# Deposit contract
# ---------------------------------------------------------------
# Execution layer chain
DEPOSIT_CHAIN_ID: {self.etb_config.get('chain-id')}
DEPOSIT_NETWORK_ID: {self.etb_config.get('network-id')}
# Allocated in Execution-layer genesis
DEPOSIT_CONTRACT_ADDRESS: {self.etb_config.get('deposit-contract-address')}
"""
