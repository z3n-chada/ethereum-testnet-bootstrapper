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


def get_potential_overrides(global_config):
    # fetch potential overrides for config-params
    overrides = {}
    cc = global_config["config-params"]["consensus-layer"]
    ec = global_config["config-params"]["execution-layer"]
    print(cc, flush=True)
    for po in potential_overrides:
        if po in cc:
            overrides[po] = cc[po]

    return overrides

def create_consensus_config(global_config):
    cp = global_config["config-params"]
    cc = global_config["config-params"]["consensus-layer"]
    ec = global_config["config-params"]["execution-layer"]
    if cc["preset-base"] == "minimal":
        # preset defaults
        pd = minimal_defaults
    elif cc["preset-base"] == "mainnet":
        # preset defaults
        pd = mainnet_defaults
    else:
        raise Exception(
            f"Invalid preset base for consensus config: {cc['preset-base']}"
        )

    overrides = get_potential_overrides(global_config)
    for k, v in overrides.items():
        pd[k] = v

    return f"""
PRESET_BASE: \"{cc['preset-base']}\"

# Genesis
# ---------------------------------------------------------------
# [customized]
MIN_GENESIS_ACTIVE_VALIDATOR_COUNT: {cc['min-genesis-active-validator-count']}

MIN_GENESIS_TIME: {global_config['now']}
GENESIS_FORK_VERSION: 0x{cc['forks']['genesis-fork-version']:08x}
GENESIS_DELAY: {cc['genesis-delay']}

# Forking
# ---------------------------------------------------------------
# Values provided for illustrative purposes.
# Individual tests/testnets may set different values.

# Altair
ALTAIR_FORK_VERSION: 0x{cc['forks']['altair-fork-version']:08x}
ALTAIR_FORK_EPOCH: {cc['forks']['altair-fork-epoch']}
# Bellatrix (aka merge)
BELLATRIX_FORK_VERSION: 0x{cc['forks']['bellatrix-fork-version']:08x}
BELLATRIX_FORK_EPOCH: {cc['forks']['bellatrix-fork-epoch']}
# Sharding
SHARDING_FORK_VERSION: 0x{cc['forks']['sharding-fork-version']:08x}
SHARDING_FORK_EPOCH: {cc['forks']['sharding-fork-epoch']}

# TBD, 2**32 is a placeholder. Merge transition approach is in active R&D.
MIN_ANCHOR_POW_BLOCK_DIFFICULTY: 4294967296

# Time parameters
# ---------------------------------------------------------------
# [customized] Faster for testing purposes
SECONDS_PER_SLOT: {pd['seconds-per-slot']}
# 14 (estimate from Eth1 mainnet)
SECONDS_PER_ETH1_BLOCK: {ec['seconds-per-eth1-block']}
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
TERMINAL_TOTAL_DIFFICULTY: {ec['terminal-total-difficulty']}
# By default, don't use these params
TERMINAL_BLOCK_HASH: {ec['terminal-block-hash']}
TERMINAL_BLOCK_HASH_ACTIVATION_EPOCH: {ec['terminal-block-hash-activation-epoch']}


# Deposit contract
# ---------------------------------------------------------------
# Execution layer chain
DEPOSIT_CHAIN_ID: {cp['deposit-chain-id']}
DEPOSIT_NETWORK_ID: {cp['deposit-network-id']}
# Allocated in Execution-layer genesis
DEPOSIT_CONTRACT_ADDRESS: {cp['deposit-contract-address']}
"""

#EPOCHS_PER_ETH1_VOTING_PERIOD: {pd['epochs-per-eth1-voting-period']}
