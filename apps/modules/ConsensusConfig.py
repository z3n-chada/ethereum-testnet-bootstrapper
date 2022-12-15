import logging

logger = logging.getLogger("bootstrapper_log")

minimal_defaults = {
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

mainnet_defaults = {
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
    'min-validator-withdrawability-delay': 1,
}

potential_overrides = ["eth1-follow-distance", "min-genesis-active-validator-count"]


def get_potential_overrides(etb_config):
    # fetch potential overrides for config-params
    cc = etb_config.config["config-params"]["consensus-layer"]
    overrides = {}
    for po in potential_overrides:
        if po in cc:
            overrides[po] = cc[po]

    return overrides


def create_consensus_config(etb_config):
    if etb_config.get("preset-base") == "minimal":
        # preset defaults
        pd = minimal_defaults
    elif etb_config.get("preset-base") == "mainnet":
        # preset defaults
        pd = mainnet_defaults
    else:
        raise Exception(
            f"Invalid preset base for consensus config: {etb_config.get_preset_base()}"
        )

    overrides = get_potential_overrides(etb_config)
    logger.debug(f"ConsensusConfig: using overrides {overrides}")
    for k, v in overrides.items():
        pd[k] = v
    return f"""
PRESET_BASE: \"{etb_config.get('preset-base')}\"
CONFIG_NAME: \"post-merge-genesis-local-testnet-0\"

# Genesis
# ---------------------------------------------------------------
# [customized]
MIN_GENESIS_ACTIVE_VALIDATOR_COUNT: {etb_config.get('min-genesis-active-validator-count')}

MIN_GENESIS_TIME: {etb_config.now}
GENESIS_FORK_VERSION: 0x{etb_config.get('genesis-fork-version'):08x}
GENESIS_DELAY: {etb_config.get('consensus-genesis-delay')}

# Forking
# ---------------------------------------------------------------
# Values provided for illustrative purposes.
# Individual tests/testnets may set different values.

# Altair
ALTAIR_FORK_VERSION: 0x{etb_config.get('altair-fork-version'):08x}
ALTAIR_FORK_EPOCH: {etb_config.get('altair-fork-epoch')}
# Bellatrix (aka merge)
BELLATRIX_FORK_VERSION: 0x{etb_config.get('bellatrix-fork-version'):08x}
BELLATRIX_FORK_EPOCH: {etb_config.get('bellatrix-fork-epoch')}

# Capella
CAPELLA_FORK_VERSION: 0x{etb_config.get('capella-fork-version'):08x}
CAPELLA_FORK_EPOCH: {etb_config.get('capella-fork-epoch')}

#EIP-4844
EIP4844_FORK_EPOCH: {etb_config.get('eip4844-fork-epoch')}

# Sharding
SHARDING_FORK_VERSION: 0x{etb_config.get('sharding-fork-version'):08x}
SHARDING_FORK_EPOCH: {etb_config.get('sharding-fork-epoch')}

# TBD, 2**32 is a placeholder. Merge transition approach is in active R&D.
MIN_ANCHOR_POW_BLOCK_DIFFICULTY: 4294967296

# Time parameters
# ---------------------------------------------------------------
# [customized] Faster for testing purposes
SECONDS_PER_SLOT: {pd['seconds-per-slot']}
# 14 (estimate from Eth1 mainnet)
SECONDS_PER_ETH1_BLOCK: {etb_config.get('seconds-per-eth1-block')}
MIN_VALIDATOR_WITHDRAWABILITY_DELAY: {pd['min-validator-withdrawability-delay']}
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
TERMINAL_TOTAL_DIFFICULTY: 0
# By default, don't use these params
TERMINAL_BLOCK_HASH: 0x0000000000000000000000000000000000000000000000000000000000000000
TERMINAL_BLOCK_HASH_ACTIVATION_EPOCH: 18446744073709551615


# Deposit contract
# ---------------------------------------------------------------
# Execution layer chain
DEPOSIT_CHAIN_ID: {etb_config.get('chain-id')}
DEPOSIT_NETWORK_ID: {etb_config.get('network-id')}
# Allocated in Execution-layer genesis
DEPOSIT_CONTRACT_ADDRESS: {etb_config.get('deposit-contract-address')}

#Updated penalty values
# ---------------------------------------------------------------
# 3 * 2**24 (= 50,331,648)
INACTIVITY_PENALTY_QUOTIENT_ALTAIR: 50331648
# 2**6 (= 64)
MIN_SLASHING_PENALTY_QUOTIENT_ALTAIR: 64
# 2
PROPORTIONAL_SLASHING_MULTIPLIER_ALTAIR: 2
# Sync committee
# ---------------------------------------------------------------
# 2**9 (= 512)
SYNC_COMMITTEE_SIZE: 512
# 2**8 (= 256)
EPOCHS_PER_SYNC_COMMITTEE_PERIOD: 256
# Sync protocol
# ---------------------------------------------------------------
# 1
MIN_SYNC_COMMITTEE_PARTICIPANTS: 1
# SLOTS_PER_EPOCH * EPOCHS_PER_SYNC_COMMITTEE_PERIOD (= 32 * 256)
UPDATE_TIMEOUT: 8192
# Mainnet preset - Bellatrix
# Updated penalty values
# ---------------------------------------------------------------
# 2**24 (= 16,777,216)
INACTIVITY_PENALTY_QUOTIENT_BELLATRIX: 16777216
# 2**5 (= 32)
MIN_SLASHING_PENALTY_QUOTIENT_BELLATRIX: 32
# 3
PROPORTIONAL_SLASHING_MULTIPLIER_BELLATRIX: 3
# Execution
# ---------------------------------------------------------------
# 2**30 (= 1,073,741,824)
MAX_BYTES_PER_TRANSACTION: 1073741824
# 2**20 (= 1,048,576)
MAX_TRANSACTIONS_PER_PAYLOAD: 1048576
# 2**8 (= 256)
BYTES_PER_LOGS_BLOOM: 256
# 2**5 (= 32)
MAX_EXTRA_DATA_BYTES: 32
# Minimal preset - Capella
# Mainnet preset - Custody Game
# Time parameters
# ---------------------------------------------------------------
# 2**1 (= 2) epochs, 12.8 minutes
RANDAO_PENALTY_EPOCHS: 2
# 2**15 (= 32,768) epochs, ~146 days
EARLY_DERIVED_SECRET_PENALTY_MAX_FUTURE_EPOCHS: 32768
# 2**14 (= 16,384) epochs ~73 days
EPOCHS_PER_CUSTODY_PERIOD: 16384
# 2**11 (= 2,048) epochs, ~9 days
CUSTODY_PERIOD_TO_RANDAO_PADDING: 2048
# 2**15 (= 32,768) epochs, ~146 days
MAX_CHUNK_CHALLENGE_DELAY: 32768
# Max operations
# ---------------------------------------------------------------
# 2**8 (= 256)
MAX_CUSTODY_KEY_REVEALS: 256
# 2**0 (= 1)
MAX_EARLY_DERIVED_SECRET_REVEALS: 1
# 2**2 (= 2)
MAX_CUSTODY_CHUNK_CHALLENGES: 4
# 2** 4 (= 16)
MAX_CUSTODY_CHUNK_CHALLENGE_RESP: 16
# 2**0 (= 1)
MAX_CUSTODY_SLASHINGS: 1
# Reward and penalty quotients
# ---------------------------------------------------------------
EARLY_DERIVED_SECRET_REVEAL_SLOT_REWARD_MULTIPLE: 2
# 2**8 (= 256)
MINOR_REWARD_QUOTIENT: 256
# Mainnet preset - Phase0
# Misc
# ---------------------------------------------------------------
# 2**6 (= 64)
MAX_COMMITTEES_PER_SLOT: 64
# 2**7 (= 128)
TARGET_COMMITTEE_SIZE: 128
# 2**11 (= 2,048)
MAX_VALIDATORS_PER_COMMITTEE: 2048
# See issue 563
SHUFFLE_ROUND_COUNT: 90
# 4
# 4
HYSTERESIS_QUOTIENT: 4

SLOTS_PER_EPOCH: 32

MAX_VALIDATORS_PER_WITHDRAWALS_SWEEP: 16384
"""


# EPOCHS_PER_ETH1_VOTING_PERIOD: {pd['epochs-per-eth1-voting-period']}
