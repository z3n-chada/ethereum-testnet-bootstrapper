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
    MinimalPreset, Epoch,
)
from .UtilityWrappers import Eth2TestnetGenesis


class ConsensusGenesisWriter(object):
    def __init__(self, etb_config: ETBConfig, logger: logging.Logger = None):
        self.etb_config: ETBConfig = etb_config
        if logger is None:
            self.logger = logging.getLogger()
        else:
            self.logger = logger

    def _get_old_version_yaml(self):
        # prysm doesn't use proper yaml for parsing.
        preset = self.etb_config.preset_base
        if preset == MinimalPreset:
            preset_name = "minimal"
        else:
            preset_name = "mainnet"

        self.logger.info(f"writing {preset_name} config.yaml")

        config_file = f"""
# Extends the {preset_name} preset
PRESET_BASE: '{preset_name}'
CONFIG_NAME: '{self.etb_config.get('config-name')}'

# Genesis
# ---------------------------------------------------------------
# `2**14` (= 16,384)
MIN_GENESIS_ACTIVE_VALIDATOR_COUNT: {self.etb_config.get('min-genesis-active-validator-count')}

# This is an invalid valid and should be updated when you create the genesis
MIN_GENESIS_TIME: {self.etb_config.get_bootstrap_genesis_time()}
GENESIS_FORK_VERSION: 0x{self.etb_config.get("phase0-fork-version"):08x}
GENESIS_DELAY: {self.etb_config.get('consensus-genesis-delay')}


# Forking
# ---------------------------------------------------------------
# Some forks are disabled for now:
#  - These may be re-assigned to another fork-version later
#  - Temporarily set to max uint64 value: 2**64 - 1

# Altair
ALTAIR_FORK_VERSION: 0x{self.etb_config.get("altair-fork-version"):08x}
ALTAIR_FORK_EPOCH: {self.etb_config.get('altair-fork-epoch')}
# Merge
BELLATRIX_FORK_VERSION: 0x{self.etb_config.get("bellatrix-fork-version"):08x}
BELLATRIX_FORK_EPOCH: {self.etb_config.get('bellatrix-fork-epoch')}

# Capella
CAPELLA_FORK_VERSION: 0x{self.etb_config.get("capella-fork-version"):08x}
CAPELLA_FORK_EPOCH: {self.etb_config.get('capella-fork-epoch')}

# Deneb
DENEB_FORK_VERSION: 0x{self.etb_config.get("deneb-fork-version"):08x}
DENEB_FORK_EPOCH: {self.etb_config.get('deneb-fork-epoch')}


TERMINAL_TOTAL_DIFFICULTY: 0
TERMINAL_BLOCK_HASH: {TerminalBlockHash}
TERMINAL_BLOCK_HASH_ACTIVATION_EPOCH: {TerminalBlockHashActivationEpoch}


# Time parameters
# ---------------------------------------------------------------
SECONDS_PER_SLOT: {self.etb_config.get_preset_value('seconds-per-slot')}
SECONDS_PER_ETH1_BLOCK: {self.etb_config.get_preset_value('seconds-per-eth1-block')}
MIN_VALIDATOR_WITHDRAWABILITY_DELAY: {self.etb_config.get_preset_value('min-validator-withdrawability-delay')}
SHARD_COMMITTEE_PERIOD: {self.etb_config.get_preset_value('shard-committee-period')}
ETH1_FOLLOW_DISTANCE: {self.etb_config.get_preset_value('eth1-follow-distance')}


# Validator cycle
# ---------------------------------------------------------------
INACTIVITY_SCORE_BIAS: {self.etb_config.get_preset_value('inactivity-score-bias')}
INACTIVITY_SCORE_RECOVERY_RATE: {self.etb_config.get_preset_value('inactivity-score-recovery-rate')}
EJECTION_BALANCE: {self.etb_config.get_preset_value('ejection-balance')}
MIN_PER_EPOCH_CHURN_LIMIT: {self.etb_config.get_preset_value('min-per-epoch-churn-limit')}
CHURN_LIMIT_QUOTIENT: {self.etb_config.get_preset_value('churn-limit-quotient')}

# Fork choice
# ---------------------------------------------------------------
# 40%
PROPOSER_SCORE_BOOST: 40

# Deposit contract
# ---------------------------------------------------------------
DEPOSIT_CHAIN_ID: {self.etb_config.get('chain-id')}
DEPOSIT_NETWORK_ID: {self.etb_config.get('network-id')}
DEPOSIT_CONTRACT_ADDRESS: {self.etb_config.config_params.get('deposit-contract-address')}
"""
        # check if we are doing a deneb experiment, if so add the deneb related config params.
        if self.etb_config.get('deneb-fork-epoch') != Epoch.FarFuture:
            config_file += f"""
# Misc
# ---------------------------------------------------------------
FIELD_ELEMENTS_PER_BLOB: {self.etb_config.get_preset_value('field-elements-per-blob')}
MAX_BLOBS_PER_BLOCK: 4
"""
        return config_file

    def create_consensus_genesis_ssz(self):
        e2tg = Eth2TestnetGenesis(self.etb_config)
        return e2tg.write_genesis_ssz()

    def create_consensus_config_yaml(self):
        return self._get_old_version_yaml()
