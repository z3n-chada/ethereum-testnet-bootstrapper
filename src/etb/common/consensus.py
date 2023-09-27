"""Consensus related constants, enums, and abstractions."""
from enum import Enum


# Preset constants and values
class PresetEnum(Enum):
    """Abstraction for the various values for a minimal or mainnet preset as
    defined in the consensus-spec."""


class Epoch(Enum):
    """Consensus Epoch constants as defined in the consensus-spec."""

    Genesis = 0
    FarFuture = 18446744073709551615


# TODO - which of these should be used in the config?
class MinimalPreset(PresetEnum, Enum):
    """Minimal presets, meant to be used for testing."""

    SLOTS_PER_EPOCH = 8
    EPOCHS_PER_ETH1_VOTING_PERIOD = 4
    # configs
    # timing
    SECONDS_PER_SLOT = 6
    SECONDS_PER_ETH1_BLOCK = 14
    MIN_VALIDATOR_WITHDRAWABILITY_DELAY = 256
    SHARD_COMMITTEE_PERIOD = 64
    ETH1_FOLLOW_DISTANCE = 16
    # validator cycle
    INACTIVITY_SCORE_BIAS = 4
    INACTIVITY_SCORE_RECOVERY_RATE = 16
    EJECTION_BALANCE = 16000000000
    MIN_PER_EPOCH_CHURN_LIMIT = 4
    CHURN_LIMIT_QUOTIENT = 32
    # fork choice
    PROPOSER_SCORE_BOOST = 40
    # networking
    GOSSIP_MAX_SIZE = 10485760
    MAX_REQUEST_BLOCKS = 1024
    EPOCHS_PER_SUBNET_SUBSCRIPTION = 256
    # MIN_VALIDATOR_WITHDRAWABILITY_DELAY + CHURN_LIMIT_QUOTIENT // 2`( = 272)
    # TODO: enforce or warn?
    MIN_EPOCHS_FOR_BLOCK_REQUESTS = 272
    MAX_CHUNK_SIZE = 10485760
    TTFB_TIMEOUT = 5
    RESP_TIMEOUT = 10
    ATTESTATION_PROPAGATION_SLOT_RANGE = 32
    MAXIMUM_GOSSIP_CLOCK_DISPARITY = 500
    MESSAGE_DOMAIN_INVALID_SNAPPY = 0x00000000
    MESSAGE_DOMAIN_VALID_SNAPPY = 0x01000000
    SUBNETS_PER_NODE = 2
    ATTESTATION_SUBNET_COUNT = 64
    ATTESTATION_SUBNET_EXTRA_BITS = 0
    ATTESTATION_SUBNET_PREFIX_BITS = 6
    # deneb
    FIELD_ELEMENTS_PER_BLOB = 4


class MainnetPreset(PresetEnum, Enum):
    """Mainnet presets, values used in mainnet."""

    # presets
    SLOTS_PER_EPOCH = 32
    EPOCHS_PER_ETH1_VOTING_PERIOD = 64
    # configs
    # timing
    SECONDS_PER_SLOT = 12
    SECONDS_PER_ETH1_BLOCK = 14
    MIN_VALIDATOR_WITHDRAWABILITY_DELAY = 256
    SHARD_COMMITTEE_PERIOD = 256
    ETH1_FOLLOW_DISTANCE = 2048
    # validator cycle
    INACTIVITY_SCORE_BIAS = 4
    INACTIVITY_SCORE_RECOVERY_RATE = 16
    EJECTION_BALANCE = 16000000000
    MIN_PER_EPOCH_CHURN_LIMIT = 4
    CHURN_LIMIT_QUOTIENT = 65536
    # fork choice
    PROPOSER_SCORE_BOOST = 40
    # networking
    GOSSIP_MAX_SIZE = 10485760
    MAX_REQUEST_BLOCKS = 1024
    EPOCHS_PER_SUBNET_SUBSCRIPTION = 256
    MIN_EPOCHS_FOR_BLOCK_REQUESTS = 33024
    MAX_CHUNK_SIZE = 10485760
    TTFB_TIMEOUT = 5
    RESP_TIMEOUT = 10
    ATTESTATION_PROPAGATION_SLOT_RANGE = 32
    MAXIMUM_GOSSIP_CLOCK_DISPARITY = 500
    MESSAGE_DOMAIN_INVALID_SNAPPY = 0x00000000
    MESSAGE_DOMAIN_VALID_SNAPPY = 0x01000000
    SUBNETS_PER_NODE = 2
    ATTESTATION_SUBNET_COUNT = 64
    ATTESTATION_SUBNET_EXTRA_BITS = 0
    ATTESTATION_SUBNET_PREFIX_BITS = 6
    # deneb
    FIELD_ELEMENTS_PER_BLOB = 4096


# Consensus values related to the merge, note that we only support post merge
# testnets, however some clients still use these values for genesis.
TerminalBlockHash: str = (
    "0x0000000000000000000000000000000000000000000000000000000000000000"
)
TerminalBlockHashActivationEpoch: int = Epoch.FarFuture.value


class ConsensusConfigOverrides(str, Enum):
    """These are the plausible overrides that users can put in the config-
    params section of an etb-config file in order to override their values.

    Do not add to this list unless you know what you are doing. They
    override the configuration of the consensus genesis files.
    """

    ETH1_FOLLOW_DISTANCE = "eth1-follow-distance"
    MIN_VALIDATOR_WITHDRAWABILITY_DELAY = "min-validator-withdrawability-delay"
    SHARD_COMMITTEE_PERIOD = "shard-committee-period"


# The full list of possible consensus forks.
DEFINED_CONSENSUS_FORK_NAMES = [
    "phase0",
    "altair",
    "bellatrix",
    "capella",
    "deneb",
    "sharding",
]


class ForkVersionName(int, Enum):
    """The code names for the forks.

    These are used in the etb-config files to define when forks happen.
    """

    phase0 = 0
    altair = 1
    bellatrix = 2
    capella = 3
    deneb = 4
    sharding = 5


class ConsensusFork:
    """Abstraction for a consensus fork."""

    def __init__(self, fork_name: ForkVersionName, fork_version: int, fork_epoch: int):
        self.name: ForkVersionName = fork_name
        self.version: int = fork_version
        self.epoch: int = fork_epoch

    def __str__(self):
        return f"{self.name.name}: 0x{self.version:02x} @ {self.epoch}"

    def __repr__(self):
        return self.__str__()
