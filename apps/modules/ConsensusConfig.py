def create_consensus_config(global_config):
    cp = global_config["config-params"]
    cc = global_config["config-params"]["consensus-layer"]
    ec = global_config["config-params"]["execution-layer"]
    return f"""
PRESET_BASE: {cc['preset-base']}

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
SECONDS_PER_SLOT: {cc['seconds-per-slot']}
# 14 (estimate from Eth1 mainnet)
SECONDS_PER_ETH1_BLOCK: {ec['seconds-per-eth1-block']}
MIN_VALIDATOR_WITHDRAWABILITY_DELAY: 256
SHARD_COMMITTEE_PERIOD: {cc['shard-committee-period']}
ETH1_FOLLOW_DISTANCE: {cc['eth1-follow-distance']}
EPOCHS_PER_ETH1_VOTING_PERIOD: {cc['epochs-per-eth1-voting-period']}

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
CHURN_LIMIT_QUOTIENT: {cc['churn-limit-quotient']}

# Transition
# ---------------------------------------------------------------
# TBD, 2**256-2**10 is a placeholder
TERMINAL_TOTAL_DIFFICULTY: {ec['genesis-config']['terminalTotalDifficulty']}
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
