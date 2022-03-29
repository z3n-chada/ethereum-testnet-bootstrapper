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
}

potential_overrides = ["eth1-follow-distance", "min-genesis-active-validator-count"]


def get_potential_overrides(etb_config):
    # fetch potential overrides for config-params
    cc = etb_config.config["config-params"]["consensus-layer"]
    overrides = {}
    print(cc, flush=True)
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
    for k, v in overrides.items():
        pd[k] = v

    return f"""
PRESET_BASE: \"{etb_config.get('preset-base')}\"

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
TERMINAL_TOTAL_DIFFICULTY: {etb_config.get('terminal-total-difficulty')}
# By default, don't use these params
TERMINAL_BLOCK_HASH: {etb_config.get('terminal-block-hash')}
TERMINAL_BLOCK_HASH_ACTIVATION_EPOCH: {etb_config.get('terminal-block-hash-activation-epoch')}


# Deposit contract
# ---------------------------------------------------------------
# Execution layer chain
DEPOSIT_CHAIN_ID: {etb_config.get('chain-id')}
DEPOSIT_NETWORK_ID: {etb_config.get('network-id')}
# Allocated in Execution-layer genesis
DEPOSIT_CONTRACT_ADDRESS: {etb_config.get('deposit-contract-address')}
"""


# EPOCHS_PER_ETH1_VOTING_PERIOD: {pd['epochs-per-eth1-voting-period']}
