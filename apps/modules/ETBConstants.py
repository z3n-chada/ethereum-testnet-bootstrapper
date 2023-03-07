"""
    This file contains default constants and enumerations that can be changed
    in one place if desired. (It is not recommended as there may be
    unintended side effects.)
"""
import re
from enum import Enum


class PresetEnum(Enum):
    pass


class Epoch(Enum):
    Genesis = 0
    FarFuture = 18446744073709551615


class MinimalPreset(PresetEnum, Enum):
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


class MainnetPreset(PresetEnum, Enum):
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


class PresetOverrides(str, Enum):
    """
    These are the plausible overrides that users can put in the
    config-params section of an etb-config file in order to
    override their values.

    Do not add to this list unless you know what you are doing.
    """

    ETH1_FOLLOW_DISTANCE = "eth1-follow-distance"
    MIN_VALIDATOR_WITHDRAWABILITY_DELAY = "min-validator-withdrawability-delay"
    SHARD_COMMITTEE_PERIOD = "shard-committee-period"


class ForkVersion(int, Enum):
    Phase0 = 0
    Altair = 1
    Bellatrix = 2
    Capella = 3
    EIP4844 = 4


class TotalDifficultyStep(int, Enum):
    Clique = 2


TerminalBlockHash = "0x0000000000000000000000000000000000000000000000000000000000000000"
TerminalBlockHashActivationEpoch = Epoch.FarFuture.value

# this regex will always match (template for regex based filtering functions)
always_match_regex = re.compile(r".*")
# this regex will ignore strings containing fuzz-ignore (for fuzzers we don't use in status-check)
fuzz_ignore_no_match_regex = re.compile(r"^((?!fuzz-ignore).)*$")
# matches hex string
hex_regex = re.compile(r"0x[0-9a-fA-F]+")
# base-10 number string
base10_number_regex = re.compile(r"[0-9]+")
