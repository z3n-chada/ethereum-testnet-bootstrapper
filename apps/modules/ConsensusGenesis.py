"""
    Contains all the necessary information and functionality to write the
    consensus config.yaml and genesis.ssz.
"""
import logging

from .ETBConfig import ETBConfig
from .Consensus import (
    ForkVersionName,
    TerminalBlockHash,
    TerminalBlockHashActivationEpoch,
    MinimalPreset, Epoch, MainnetPreset,
)
from .UtilityWrappers import Eth2TestnetGenesis


class ConsensusGenesisWriter(object):
    def __init__(self, etb_config: ETBConfig, logger: logging.Logger = None):
        # self.etb_config: ETBConfig = etb_config
        if etb_config.genesis_time is None:
            raise Exception("Genesis time must be set.") # should not occur
        self.etb_config = etb_config
        self.consensus_testnet_config = etb_config.testnet_config.consensus_layer
        if logger is None:
            self.logger = logging.getLogger()
        else:
            self.logger = logger

    def _get_old_version_yaml(self):
        # prysm doesn't use proper yaml for parsing.
        preset = self.consensus_testnet_config.preset_base
        if preset == MinimalPreset:
            preset_name = "minimal"
        elif preset == MainnetPreset:
            preset_name = "mainnet"
        else:
            raise Exception(f"Unknown preset: {preset}")

        # handle potential overrides


        self.logger.info(f"writing {preset_name} config.yaml")

        config_file = f"""
# Extends the {preset_name} preset
PRESET_BASE: '{preset_name}'
CONFIG_NAME: '{self.consensus_testnet_config.config_name}'

# Genesis
# ---------------------------------------------------------------
# `2**14` (= 16,384)
MIN_GENESIS_ACTIVE_VALIDATOR_COUNT: {self.consensus_testnet_config.min_genesis_active_validator_count}

# This is an invalid valid and should be updated when you create the genesis
MIN_GENESIS_TIME: {self.etb_config.genesis_time}
GENESIS_FORK_VERSION: 0x{self.consensus_testnet_config.phase0_fork.version:08x}
# genesis delay no longer supported
GENESIS_DELAY: 0


# Forking
# ---------------------------------------------------------------
# Some forks are disabled for now:
#  - These may be re-assigned to another fork-version later
#  - Temporarily set to max uint64 value: 2**64 - 1

# Altair
ALTAIR_FORK_VERSION: 0x{self.consensus_testnet_config.altair_fork.version:08x}
ALTAIR_FORK_EPOCH: {self.consensus_testnet_config.altair_fork.epoch}
# Merge
BELLATRIX_FORK_VERSION: 0x{self.consensus_testnet_config.bellatrix_fork.version:08x}
BELLATRIX_FORK_EPOCH: {self.consensus_testnet_config.bellatrix_fork.epoch}

# Capella
CAPELLA_FORK_VERSION: 0x{self.consensus_testnet_config.capella_fork.version:08x}
CAPELLA_FORK_EPOCH: {self.consensus_testnet_config.capella_fork.epoch}

# Deneb
DENEB_FORK_VERSION: 0x{self.consensus_testnet_config.deneb_fork.version:08x}
DENEB_FORK_EPOCH: {self.consensus_testnet_config.deneb_fork.epoch}


TERMINAL_TOTAL_DIFFICULTY: 0
TERMINAL_BLOCK_HASH: {self.consensus_testnet_config.terminal_block_hash}
TERMINAL_BLOCK_HASH_ACTIVATION_EPOCH: {self.consensus_testnet_config.terminal_block_hash_activation_epoch}


# Time parameters
# ---------------------------------------------------------------
SECONDS_PER_SLOT: {self.consensus_testnet_config.preset_base.SECONDS_PER_SLOT.value}
SECONDS_PER_ETH1_BLOCK: {self.consensus_testnet_config.preset_base.SECONDS_PER_ETH1_BLOCK.value}
# potential override
MIN_VALIDATOR_WITHDRAWABILITY_DELAY: {self.consensus_testnet_config.min_validator_withdrawability_delay}
# potential override
SHARD_COMMITTEE_PERIOD: {self.consensus_testnet_config.shard_committee_period}
ETH1_FOLLOW_DISTANCE: {self.consensus_testnet_config.preset_base.ETH1_FOLLOW_DISTANCE.value}


# Validator cycle
# ---------------------------------------------------------------
INACTIVITY_SCORE_BIAS: {self.consensus_testnet_config.preset_base.INACTIVITY_SCORE_BIAS.value}
INACTIVITY_SCORE_RECOVERY_RATE: {self.consensus_testnet_config.preset_base.INACTIVITY_SCORE_RECOVERY_RATE.value}
EJECTION_BALANCE: {self.consensus_testnet_config.preset_base.EJECTION_BALANCE.value}
MIN_PER_EPOCH_CHURN_LIMIT: {self.consensus_testnet_config.preset_base.MIN_PER_EPOCH_CHURN_LIMIT.value}
CHURN_LIMIT_QUOTIENT: {self.consensus_testnet_config.preset_base.CHURN_LIMIT_QUOTIENT.value}

# Fork choice
# ---------------------------------------------------------------
# 40%
PROPOSER_SCORE_BOOST: 40

# Deposit contract
# ---------------------------------------------------------------
DEPOSIT_CHAIN_ID: {self.etb_config.testnet_config.execution_layer.chain_id}
DEPOSIT_NETWORK_ID: {self.etb_config.testnet_config.execution_layer.network_id}
DEPOSIT_CONTRACT_ADDRESS: {self.etb_config.testnet_config.deposit_contract_address}
"""
        # check if we are doing a deneb experiment, if so add the deneb related config params.
        if self.consensus_testnet_config.deneb_fork.epoch != Epoch.FarFuture:
            config_file += f"""
# Misc
# ---------------------------------------------------------------
FIELD_ELEMENTS_PER_BLOB: {self.consensus_testnet_config.preset_base.FIELD_ELEMENTS_PER_BLOB.value}
MAX_BLOBS_PER_BLOCK: 4
"""
        return config_file

    def create_consensus_genesis_ssz(self):
        e2tg = Eth2TestnetGenesis(self.etb_config, self.logger)
        return e2tg.write_genesis_ssz()

    def create_consensus_config_yaml(self):
        return self._get_old_version_yaml()
