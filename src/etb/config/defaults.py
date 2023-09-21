"""
    Contains all the default configuration values for when etb-config parameters are left blank.
"""

# testnet-config
DEFAULT_DEPOSIT_CONTRACT_ADDRESS = "0x8c594691c0e592ffa21f153a16ae41db5befcaaa"

# testnet-config -> execution-layer
DEFAULT_SECONDS_PER_ETH1_BLOCK = 14
DEFAULT_CHAIN_ID = 1337
DEFAULT_NETWORK_ID = 1337

DEFAULT_EXECUTION_ACCOUNT_MNEMONIC = "cat swing flag economy stadium alone churn speed unique patch report train"
DEFAULT_EXECUTION_KEYSTORE_PASSPHRASE = "testnet-password"

DEFAULT_PREMINES = {
    "m/44'/60'/0'/0/0": 100000000,
    "m/44'/60'/0'/0/1": 100000000,
    "m/44'/60'/0'/0/2": 100000000,
    "m/44'/60'/0'/0/3": 100000000,
}

# testnet-config -> consensus-layer
DEFAULT_CONFIG_NAME = "local-minimal-testnet"

DEFAULT_VALIDATOR_MNEMONIC = ("ocean style run case glory clip into nature guess jacket document firm fiscal hello "
                              "kite disagree symptom tide net coral envelope wink render festival")

DEFAULT_PHASE0_FORK_VERSION = 0x01000666
DEFAULT_ALTAIR_FORK_VERSION = 0x02000666
DEFAULT_BELLATRIX_FORK_VERSION = 0x03000666
DEFAULT_CAPELLA_FORK_VERSION = 0x04000666
DEFAULT_DENEB_FORK_VERSION = 0x05000666
DEFAULT_SHARDING_FORK_VERSION = 0x06000666

DEFAULT_PHASE0_FORK_EPOCH = 0
DEFAULT_ALTAIR_FORK_EPOCH = 0
DEFAULT_BELLATRIX_FORK_EPOCH = 0
DEFAULT_CAPELLA_FORK_EPOCH = 2
DEFAULT_DENEB_FORK_EPOCH = 18446744073709551615
DEFAULT_SHARDING_FORK_EPOCH = 18446744073709551615

# execution-configs
DEFAULT_EXECUTION_CLIENT_CONFIG_NAME_GETH = "geth-execution-config"
DEFAULT_EXECUTION_CLIENT_CONFIG_NAME_RETH = "reth-execution-config"
DEFAULT_EXECUTION_CLIENT_CONFIG_NAME_BESU = "besu-execution-config"
DEFAULT_EXECUTION_CLIENT_CONFIG_NAME_NETHERMIND = "nethermind-execution-config"
# launchers
DEFAULT_EXECUTION_LAUNCHER_GETH = "/source/deps/launchers/el/launch-geth.sh"
DEFAULT_EXECUTION_LAUNCHER_RETH = "/source/deps/launchers/el/launch-reth.sh"
DEFAULT_EXECUTION_LAUNCHER_BESU = "/source/deps/launchers/el/launch-besu.sh"
DEFAULT_EXECUTION_LAUNCHER_NETHERMIND = "/source/deps/launchers/el/launch-nethermind.sh"

DEFAULT_EXECUTION_APIS_GETH = "admin,net,eth,web3,engine"
DEFAULT_EXECUTION_APIS_BESU = "ADMIN,ETH,NET,TXPOOL,WEB3,ENGINE"
DEFAULT_EXECUTION_APIS_NETHERMIND = "net,eth,consensus,subscribe,web3,admin"
DEFAULT_EXECUTION_APIS_RETH = "eth,net,admin,web3"

DEFAULT_EXECUTION_LOG_LEVEL_GETH = "4"
DEFAULT_EXECUTION_LOG_LEVEL_RETH = "4"
DEFAULT_EXECUTION_LOG_LEVEL_BESU = "info"
DEFAULT_EXECUTION_LOG_LEVEL_NETHERMIND = "INFO"
# networking and config
DEFAULT_EXECUTION_HTTP_PORT = 8645
DEFAULT_EXECUTION_WS_PORT = 8646
DEFAULT_EXECUTION_P2P_PORT = 30303
DEFAULT_EXECUTION_ENGINE_HTTP_PORT = 8551
DEFAULT_EXECUTION_ENGINE_WS_PORT = 8552
DEFAULT_EXECUTION_METRIC_PORT = 6060

# consensus-configs
DEFAULT_CONSENSUS_CLIENT_CONFIG_NAME_TEKU = "teku-consensus-client"
DEFAULT_CONSENSUS_CLIENT_CONFIG_NAME_PRYSM = "prysm-consensus-client"
DEFAULT_CONSENSUS_CLIENT_CONFIG_NAME_NIMBUS = "nimbus-consensus-client"
DEFAULT_CONSENSUS_CLIENT_CONFIG_NAME_LIGHTHOUSE = "lighthouse-consensus-client"
DEFAULT_CONSENSUS_CLIENT_CONFIG_NAME_LODESTAR = "lodestar-consensus-client"

# launchers
DEFAULT_CONSENSUS_LAUNCHER_PRYSM = "/source/deps/launchers/cl/launch-prysm.sh"
DEFAULT_CONSENSUS_LAUNCHER_NIMBUS = "/source/deps/launchers/cl/launch-nimbus.sh"
DEFAULT_CONSENSUS_LAUNCHER_TEKU = "/source/deps/launchers/cl/launch-teku.sh"
DEFAULT_CONSENSUS_LAUNCHER_LIGHTHOUSE = "/source/deps/launchers/cl/launch-lighthouse.sh"
DEFAULT_CONSENSUS_LAUNCHER_LODESTAR = "/source/deps/launchers/cl/launch-lodestar.sh"

# log level
DEFAULT_CONSENSUS_LOG_LEVEL_PRYSM = "info"
DEFAULT_CONSENSUS_LOG_LEVEL_NIMBUS = "info"
DEFAULT_CONSENSUS_LOG_LEVEL_TEKU = "INFO"
DEFAULT_CONSENSUS_LOG_LEVEL_LIGHTHOUSE = "info"
DEFAULT_CONSENSUS_LOG_LEVEL_LODESTAR = "info"

# configs
DEFAULT_NUM_VALIDATORS = 4
DEFAULT_CONSENSUS_P2P_TCP_PORT = 13000
DEFAULT_CONSENSUS_P2P_UDP_PORT = 12000
DEFAULT_CONSENSUS_BEACON_API_PORT = 5052
DEFAULT_CONSENSUS_BEACON_RPC_PORT = 3500
DEFAULT_CONSENSUS_BEACON_METRIC_PORT = 8080
DEFAULT_CONSENSUS_VALIDATOR_METRIC_PORT = 8081
DEFAULT_CONSENSUS_VALIDATOR_RPC_PORT = 7000

# consensus-configs (client specific)
DEFAULT_PRYSM_VALIDATOR_PASSWORD = "testnet-password"
DEFAULT_LODESTAR_MINIMAL_CONFIG_ENV = {"LODESTAR_PRESET": "minimal"}

# docker images and tags
DEFAULT_MINIMAL_DOCKER_IMAGE = "etb-all-clients"
DEFAULT_MINIMAL_DOCKER_TAG = "minimal-current"
DEFAULT_MAINNET_DOCKER_IMAGE = "etb-all-clients"
DEFAULT_MAINNET_DOCKER_TAG = "mainnet-current"

# full consensus template configs
# DEFAULT_CONSENSUS_CONFIG_PRYSM = {
#     "client": "prysm",
#     "launcher": DEFAULT_CONSENSUS_LAUNCHER_PRYSM,
#     "log-level": DEFAULT_CONSENSUS_LOG_LEVEL_PRYSM,
#     "beacon-api-port": DEFAULT_CONSENSUS_BEACON_API_PORT,
#     "beacon-rpc-port": DEFAULT_CONSENSUS_BEACON_RPC_PORT,
#     "beacon-metric-port": DEFAULT_CONSENSUS_BEACON_METRIC_PORT,
#     "validator-rpc-port": DEFAULT_CONSENSUS_VALIDATOR_RPC_PORT,
#     "validator-metric-port": DEFAULT_CONSENSUS_VALIDATOR_METRIC_PORT,
#     "num-validators": DEFAULT_NUM_VALIDATORS,
# }
# DEFAULT_CONSENSUS_CONFIG_TEKU = {
#     "client": "teku",
#     "launcher": DEFAULT_CONSENSUS_LAUNCHER_TEKU,
#     "log-level": DEFAULT_CONSENSUS_LOG_LEVEL_TEKU,
#     "beacon-api-port": DEFAULT_CONSENSUS_BEACON_API_PORT,
#     "beacon-rpc-port": DEFAULT_CONSENSUS_BEACON_RPC_PORT,
#     "beacon-metric-port": DEFAULT_CONSENSUS_BEACON_METRIC_PORT,
#     "validator-rpc-port": DEFAULT_CONSENSUS_VALIDATOR_RPC_PORT,
#     "validator-metric-port": DEFAULT_CONSENSUS_VALIDATOR_METRIC_PORT,
#     "num-validators": DEFAULT_NUM_VALIDATORS,
# }
#
# DEFAULT_CONSENSUS_CONFIG_NIMBUS = {
#     "client": "nimbus",
#     "launcher": DEFAULT_CONSENSUS_LAUNCHER_NIMBUS,
#     "log-level": DEFAULT_CONSENSUS_LOG_LEVEL_NIMBUS,
#     "beacon-api-port": DEFAULT_CONSENSUS_BEACON_API_PORT,
#     "beacon-rpc-port": DEFAULT_CONSENSUS_BEACON_RPC_PORT,
#     "beacon-metric-port": DEFAULT_CONSENSUS_BEACON_METRIC_PORT,
#     "validator-rpc-port": DEFAULT_CONSENSUS_VALIDATOR_RPC_PORT,
#     "validator-metric-port": DEFAULT_CONSENSUS_VALIDATOR_METRIC_PORT,
#     "num-validators": DEFAULT_NUM_VALIDATORS,
# }
#
# DEFAULT_CONSENSUS_CONFIG_LIGHTHOUSE = {
#     "client": "lighthouse",
#     "launcher": DEFAULT_CONSENSUS_LAUNCHER_LIGHTHOUSE,
#     "log-level": DEFAULT_CONSENSUS_LOG_LEVEL_LIGHTHOUSE,
#     "beacon-api-port": DEFAULT_CONSENSUS_BEACON_API_PORT,
#     "beacon-rpc-port": DEFAULT_CONSENSUS_BEACON_RPC_PORT,
#     "beacon-metric-port": DEFAULT_CONSENSUS_BEACON_METRIC_PORT,
#     "validator-rpc-port": DEFAULT_CONSENSUS_VALIDATOR_RPC_PORT,
#     "validator-metric-port": DEFAULT_CONSENSUS_VALIDATOR_METRIC_PORT,
#     "num-validators": DEFAULT_NUM_VALIDATORS,
# }
#
# DEFAULT_CONSENSUS_CONFIG_LODESTAR = {
#     "client": "lodestar",
#     "launcher": DEFAULT_CONSENSUS_LAUNCHER_LODESTAR,
#     "log-level": DEFAULT_CONSENSUS_LOG_LEVEL_LODESTAR,
#     "beacon-api-port": DEFAULT_CONSENSUS_BEACON_API_PORT,
#     "beacon-rpc-port": DEFAULT_CONSENSUS_BEACON_RPC_PORT,
#     "beacon-metric-port": DEFAULT_CONSENSUS_BEACON_METRIC_PORT,
#     "validator-rpc-port": DEFAULT_CONSENSUS_VALIDATOR_RPC_PORT,
#     "validator-metric-port": DEFAULT_CONSENSUS_VALIDATOR_METRIC_PORT,
#     "num-validators": DEFAULT_NUM_VALIDATORS,
# }

# default config maps
DEFAULT_CONSENSUS_CLIENT_SPECIFIC_VALUES_MAP = {
    ("prysm", "log-level"): DEFAULT_CONSENSUS_LOG_LEVEL_PRYSM,
    ("teku", "log-level"): DEFAULT_CONSENSUS_LOG_LEVEL_TEKU,
    ("lodestar", "log-level"): DEFAULT_CONSENSUS_LOG_LEVEL_LODESTAR,
    ("nimbus", "log-level"): DEFAULT_CONSENSUS_LOG_LEVEL_NIMBUS,
    ("lighthouse", "log-level"): DEFAULT_CONSENSUS_LOG_LEVEL_LIGHTHOUSE,
    ("prysm", "launcher"): DEFAULT_CONSENSUS_LAUNCHER_PRYSM,
    ("teku", "launcher"): DEFAULT_CONSENSUS_LAUNCHER_TEKU,
    ("lodestar", "launcher"): DEFAULT_CONSENSUS_LAUNCHER_LODESTAR,
    ("nimbus", "launcher"): DEFAULT_CONSENSUS_LAUNCHER_NIMBUS,
    ("lighthouse", "launcher"): DEFAULT_CONSENSUS_LAUNCHER_LIGHTHOUSE,
}

DEFAULT_CONSENSUS_VALUES_MAP = {
    "p2p-port": DEFAULT_CONSENSUS_P2P_TCP_PORT,
    "beacon-api-port": DEFAULT_CONSENSUS_BEACON_API_PORT,
    "beacon-rpc-port": DEFAULT_CONSENSUS_BEACON_RPC_PORT,
    "beacon-metric-port": DEFAULT_CONSENSUS_BEACON_METRIC_PORT,
    "validator-rpc-port": DEFAULT_CONSENSUS_VALIDATOR_RPC_PORT,
    "validator-metric-port": DEFAULT_CONSENSUS_VALIDATOR_METRIC_PORT,
    "num-validators": DEFAULT_NUM_VALIDATORS,
}
