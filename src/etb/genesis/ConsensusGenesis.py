"""
    Contains all the necessary information and functionality to write the
    consensus config.yaml and genesis.ssz.
"""
import logging

from ..config.ETBConfig import ETBConfig
from ..common.Consensus import (
    ForkVersionName,
    MinimalPreset, Epoch, MainnetPreset, ConsensusFork,
)

from ..interfaces.external.Eth2TestnetGenesis import Eth2TestnetGenesis


class ConsensusGenesisWriter(object):
    def __init__(self, etb_config: ETBConfig, logger: logging.Logger = None):
        # self.etb_config: ETBConfig = etb_config
        if etb_config.genesis_time is None:
            raise Exception("Genesis time must be set.")  # should not occur
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

# Networking
# ---------------------------------------------------------------
GOSSIP_MAX_SIZE: {self.consensus_testnet_config.preset_base.GOSSIP_MAX_SIZE.value}
MAX_CHUNK_SIZE: {self.consensus_testnet_config.preset_base.MAX_CHUNK_SIZE.value}
MAX_REQUEST_BLOCKS: {self.consensus_testnet_config.preset_base.MAX_REQUEST_BLOCKS.value}
EPOCHS_PER_SUBNET_SUBSCRIPTION: {self.consensus_testnet_config.preset_base.EPOCHS_PER_SUBNET_SUBSCRIPTION.value}
SUBNETS_PER_NODE: {self.consensus_testnet_config.preset_base.SUBNETS_PER_NODE.value}
ATTESTATION_SUBNET_COUNT: {self.consensus_testnet_config.preset_base.ATTESTATION_SUBNET_COUNT.value}
ATTESTATION_SUBNET_EXTRA_BITS: {self.consensus_testnet_config.preset_base.ATTESTATION_SUBNET_EXTRA_BITS.value}
ATTESTATION_SUBNET_PREFIX_BITS: {self.consensus_testnet_config.preset_base.ATTESTATION_SUBNET_PREFIX_BITS.value}
TTFB_TIMEOUT: {self.consensus_testnet_config.preset_base.TTFB_TIMEOUT.value}
RESP_TIMEOUT: {self.consensus_testnet_config.preset_base.RESP_TIMEOUT.value}
ATTESTATION_PROPAGATION_SLOT_RANGE: {self.consensus_testnet_config.preset_base.ATTESTATION_PROPAGATION_SLOT_RANGE.value}
MAXIMUM_GOSSIP_CLOCK_DISPARITY: {self.consensus_testnet_config.preset_base.MAXIMUM_GOSSIP_CLOCK_DISPARITY.value}
MESSAGE_DOMAIN_INVALID_SNAPPY: 0x00000000
MESSAGE_DOMAIN_VALID_SNAPPY: 0x01000000

# potential override
# MIN_VALIDATOR_WITHDRAWABILITY_DELAY + CHURN_LIMIT_QUOTIENT // 2
MIN_EPOCHS_FOR_BLOCK_REQUESTS: {self.consensus_testnet_config.min_epochs_for_block_requests}

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

    def create_consensus_genesis_ssz(self) -> bytes:
        """
        Create the consensus genesis state and return the SSZ encoded bytes.
        @return: genesis_ssz as bytes
        """
        validator_mnemonic = self.etb_config.testnet_config.consensus_layer.validator_mnemonic
        num_validators = self.etb_config.testnet_config.consensus_layer.min_genesis_active_validator_count
        genesis_fork: ConsensusFork = self.etb_config.testnet_config.consensus_layer.get_genesis_fork()

        eth2_testnet_genesis = Eth2TestnetGenesis(validator_mnemonic=validator_mnemonic, num_validators=num_validators)

        # set all of the preset args
        preset_args = []
        preset = self.etb_config.testnet_config.consensus_layer.preset_base
        if preset == MinimalPreset:
            preset_base_str = "minimal"
        elif preset == MainnetPreset:
            preset_base_str = "mainnet"
        else:
            raise Exception(f"Unknown preset: {preset}")  # should never happen

        if genesis_fork.name >= ForkVersionName.phase0:
            preset_args.append("--preset-phase0")
            preset_args.append(preset_base_str)

        if genesis_fork.name >= ForkVersionName.altair:
            preset_args.append("--preset-altair")
            preset_args.append(preset_base_str)

        if genesis_fork.name >= ForkVersionName.bellatrix:
            preset_args.append("--preset-bellatrix")
            preset_args.append(preset_base_str)
            preset_args.append("--eth1-config")
            preset_args.append(str(self.etb_config.files.geth_genesis_file))

        if genesis_fork.name >= ForkVersionName.capella:
            preset_args.append("--preset-capella")
            preset_args.append(preset_base_str)

        out = eth2_testnet_genesis.get_genesis_ssz(genesis_fork_name=genesis_fork.name.name.lower(),
                                                   config_in=self.etb_config.files.consensus_config_file,
                                                   genesis_ssz_out=self.etb_config.files.consensus_genesis_file,
                                                   preset_args=preset_args)
        # there was an issue
        if isinstance(out, Exception):
            raise out

        return out

    def create_consensus_config_yaml(self):
        return self._get_old_version_yaml()
