"""
    Contains all the default configuration values for when etb-config parameters are left blank.
"""

from ..common.consensus import Epoch

DEFAULT_IP_PREFIX = "10.0.20."  # IP that we iterate from

# docker
DEFAULT_DOCKER_NETWORK_NAME = "ethereum-testnet"
DEFAULT_DOCKER_IP_SUBNET = DEFAULT_IP_PREFIX + "0/24"
DEFAULT_DOCKER_VOLUMES = ['./data:/data/', './:/source/']

DEFAULT_DOCKER_CONFIG = {
    "network-name": DEFAULT_DOCKER_NETWORK_NAME,
    "ip-subnet": DEFAULT_DOCKER_IP_SUBNET,
    "volumes": DEFAULT_DOCKER_VOLUMES,
}

# files
DEFAULT_TESTNET_ROOT = "/data/"
DEFAULT_GETH_GENESIS_FILE = "/data/geth-genesis.json"
DEFAULT_BESU_GENESIS_FILE = "/data/besu-genesis.json"
DEFAULT_NETHERMIND_GENESIS_FILE = "/data/nethermind-genesis.json"
DEFAULT_CONSENSUS_CONFIG_FILE = "/data/config.yaml"
DEFAULT_CONSENSUS_GENESIS_FILE = "/data/genesis.ssz"
DEFAULT_CONSENSUS_BOOTNODES_FILE = "/data/consensus-bootnodes.txt"
DEFAULT_ETB_CONFIG_FILE = "/data/etb-config.yaml"
DEFAULT_LOCAL_TESTNET_DIR = "/data/local-testnet/"
DEFAULT_DOCKER_COMPOSE_FILE = "/source/docker-compose.yaml"  # used by host so use /source/
DEFAULT_ETB_CONFIG_CHECKPOINT_FILE = "/data/etb-config-checkpoint.txt"
DEFAULT_CONSENSUS_CHECKPOINT_FILE = "/data/consensus-checkpoint.txt"
DEFAULT_EXECUTION_CHECKPOINT_FILE = "/data/execution-checkpoint.txt"
DEFAULT_CONSENSUS_BOOTNODE_CHECKPOINT_FILE = "/data/consensus-bootnode-checkpoint.txt"
DEFAULT_DEPOSIT_CONTRACT_DEPLOYMENT_BLOCK_HASH_FILE = "/data/deposit-contract-deployment-block-hash.txt"
DEFAULT_DEPOSIT_CONTRACT_DEPLOYMENT_BLOCK_NUMBER_FILE = "/data/deposit-contract-deployment-block-number.txt"
DEFAULT_TRUSTED_SETUP_TXT_FILE = "/data/trusted-setup.txt"
DEFAULT_TRUSTED_SETUP_JSON_FILE = "/data/trusted-setup.json"

DEFAULT_FILES_CONFIG = {
    "testnet-root": DEFAULT_TESTNET_ROOT,
    "geth-genesis-file": DEFAULT_GETH_GENESIS_FILE,
    "besu-genesis-file": DEFAULT_BESU_GENESIS_FILE,
    "nether-mind-genesis-file": DEFAULT_NETHERMIND_GENESIS_FILE,
    "consensus-config-file": DEFAULT_CONSENSUS_CONFIG_FILE,
    "consensus-genesis-file": DEFAULT_CONSENSUS_GENESIS_FILE,
    "consensus-bootnode-file": DEFAULT_CONSENSUS_BOOTNODES_FILE,
    "etb-config-file": DEFAULT_ETB_CONFIG_FILE,
    "local-testnet-dir": DEFAULT_LOCAL_TESTNET_DIR,
    "docker-compose-file": DEFAULT_DOCKER_COMPOSE_FILE,
    "etb-config-checkpoint-file": DEFAULT_ETB_CONFIG_CHECKPOINT_FILE,
    "consensus-checkpoint-file": DEFAULT_CONSENSUS_CHECKPOINT_FILE,
    "execution-checkpoint-file": DEFAULT_EXECUTION_CHECKPOINT_FILE,
    "consensus-bootnode-checkpoint-file": DEFAULT_CONSENSUS_BOOTNODE_CHECKPOINT_FILE,
    "deposit-contract-deployment-block-hash-file": DEFAULT_DEPOSIT_CONTRACT_DEPLOYMENT_BLOCK_HASH_FILE,
    "deposit-contract-deployment-block-number-file": DEFAULT_DEPOSIT_CONTRACT_DEPLOYMENT_BLOCK_NUMBER_FILE,
}

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

DEFAULT_TESTNET_EXECUTION_CONFIG = {
    "seconds-per-eth1-block": DEFAULT_SECONDS_PER_ETH1_BLOCK,
    "chain-id": DEFAULT_CHAIN_ID,
    "network-id": DEFAULT_NETWORK_ID,
    "account-mnemonic": DEFAULT_EXECUTION_ACCOUNT_MNEMONIC,
    "keystore-passphrase": DEFAULT_EXECUTION_KEYSTORE_PASSPHRASE,
    "premines": DEFAULT_PREMINES,
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
DEFAULT_DENEB_FORK_EPOCH = Epoch.FarFuture.value
DEFAULT_SHARDING_FORK_EPOCH = Epoch.FarFuture.value

DEFAULT_TESTNET_CONSENSUS_CONFIG = {
    "config-name": DEFAULT_CONFIG_NAME,
    "validator-mnemonic": DEFAULT_VALIDATOR_MNEMONIC,
    "phase0-fork-version": DEFAULT_PHASE0_FORK_VERSION,
    "phase0-fork-epoch": DEFAULT_PHASE0_FORK_EPOCH,
    "altair-fork-version": DEFAULT_ALTAIR_FORK_VERSION,
    "altair-fork-epoch": DEFAULT_ALTAIR_FORK_EPOCH,
    "bellatrix-fork-version": DEFAULT_BELLATRIX_FORK_VERSION,
    "bellatrix-fork-epoch": DEFAULT_BELLATRIX_FORK_EPOCH,
    "capella-fork-version": DEFAULT_CAPELLA_FORK_VERSION,
    "capella-fork-epoch": DEFAULT_CAPELLA_FORK_EPOCH,
    "deneb-fork-version": DEFAULT_DENEB_FORK_VERSION,
    "deneb-fork-epoch": DEFAULT_DENEB_FORK_EPOCH,
    "sharding-fork-version": DEFAULT_SHARDING_FORK_VERSION,
    "sharding-fork-epoch": DEFAULT_SHARDING_FORK_EPOCH,
}

DEFAULT_TESTNET_CONFIG = {
    "deposit-contract-address": DEFAULT_DEPOSIT_CONTRACT_ADDRESS,
    "execution-layer": DEFAULT_TESTNET_EXECUTION_CONFIG,
    "consensus-layer": DEFAULT_TESTNET_CONSENSUS_CONFIG
}
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
DEFAULT_EXECUTION_LOG_LEVEL_RETH = "vvvv"
DEFAULT_EXECUTION_LOG_LEVEL_BESU = "info"
DEFAULT_EXECUTION_LOG_LEVEL_NETHERMIND = "INFO"
# networking and config
DEFAULT_EXECUTION_HTTP_PORT = 8645
DEFAULT_EXECUTION_WS_PORT = 8646
DEFAULT_EXECUTION_P2P_PORT = 30303
DEFAULT_EXECUTION_ENGINE_HTTP_PORT = 8551
DEFAULT_EXECUTION_ENGINE_WS_PORT = 8551
DEFAULT_EXECUTION_ENGINE_WS_PORT_NETHERMIND = 8552  # nethermind needs a separate ws-port
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
DEFAULT_CONSENSUS_P2P_PORT = 9000
DEFAULT_CONSENSUS_BEACON_API_PORT = 5052
DEFAULT_CONSENSUS_BEACON_RPC_PORT = 3500
DEFAULT_CONSENSUS_BEACON_METRIC_PORT = 8080
DEFAULT_CONSENSUS_VALIDATOR_METRIC_PORT = 8081
DEFAULT_CONSENSUS_VALIDATOR_RPC_PORT = 7000

# consensus-configs (client specific)
DEFAULT_PRYSM_VALIDATOR_PASSWORD = "testnet-password"
DEFAULT_LODESTAR_MINIMAL_CONFIG_ENV = {"LODESTAR_PRESET": "minimal"}

DEFAULT_CONSENSUS_CLIENT_INSTANCE_ADDITIONAL_ENV = {
    "mainnet": {
        "prysm": {"validator-password": DEFAULT_PRYSM_VALIDATOR_PASSWORD},
        "lodestar" : {},
        "teku": {},
        "nimbus": {},
        "lighthouse": {},
    },
    "minimal": {
        "prysm": {"validator-password": DEFAULT_PRYSM_VALIDATOR_PASSWORD},
        "lodestar": {"lodestar-preset": "minimal"},
        "teku": {},
        "nimbus": {},
        "lighthouse": {},
    }
}

# docker images and tags
DEFAULT_MINIMAL_DOCKER_IMAGE = "etb-all-clients"
DEFAULT_MINIMAL_DOCKER_TAG = "minimal-current"
DEFAULT_MAINNET_DOCKER_IMAGE = "etb-all-clients"
DEFAULT_MAINNET_DOCKER_TAG = "mainnet-current"

DEFAULT_EXECUTION_CONFIG_FIELDS = [
    "launcher",
    "log-level",
    "p2p-port",
    "http-apis",
    "http-port",
    "ws-apis",
    "ws-port",
    "engine-http-port",
    "engine-ws-port",
    "metric-port",
]
# default config maps
DEFAULT_EXECUTION_CLIENT_SPECIFIC_VALUES_MAP = {
    ("geth", "launcher"): DEFAULT_EXECUTION_LAUNCHER_GETH,
    ("geth", "log-level"): DEFAULT_EXECUTION_LOG_LEVEL_GETH,
    ("geth", "ws-apis"): DEFAULT_EXECUTION_APIS_GETH,
    ("geth", "http-apis"): DEFAULT_EXECUTION_APIS_GETH,
    ("besu", "launcher"): DEFAULT_EXECUTION_LAUNCHER_BESU,
    ("besu", "log-level"): DEFAULT_EXECUTION_LOG_LEVEL_BESU,
    ("besu", "ws-apis"): DEFAULT_EXECUTION_APIS_BESU,
    ("besu", "http-apis"): DEFAULT_EXECUTION_APIS_BESU,
    ("reth", "launcher"): DEFAULT_EXECUTION_LAUNCHER_RETH,
    ("reth", "log-level"): DEFAULT_EXECUTION_LOG_LEVEL_RETH,
    ("reth", "ws-apis"): DEFAULT_EXECUTION_APIS_RETH,
    ("reth", "http-apis"): DEFAULT_EXECUTION_APIS_RETH,
    ("nethermind", "launcher"): DEFAULT_EXECUTION_LAUNCHER_NETHERMIND,
    ("nethermind", "log-level"): DEFAULT_EXECUTION_LOG_LEVEL_NETHERMIND,
    ("nethermind", "ws-apis"): DEFAULT_EXECUTION_APIS_NETHERMIND,
    ("nethermind", "http-apis"): DEFAULT_EXECUTION_APIS_NETHERMIND,
    ("nethermind", "engine-ws-port"): DEFAULT_EXECUTION_ENGINE_WS_PORT_NETHERMIND,
}

DEFAULT_EXECUTION_VALUES_MAP = {
    "engine-http-port": DEFAULT_EXECUTION_ENGINE_HTTP_PORT,
    "engine-ws-port": DEFAULT_EXECUTION_ENGINE_WS_PORT,
    "p2p-port": DEFAULT_EXECUTION_P2P_PORT,
    "http-port": DEFAULT_EXECUTION_HTTP_PORT,
    "ws-port": DEFAULT_EXECUTION_WS_PORT,
    "metric-port": DEFAULT_EXECUTION_METRIC_PORT,
}

DEFAULT_EXECUTION_CONFIG = {
    DEFAULT_EXECUTION_CLIENT_CONFIG_NAME_GETH: {"client": "geth"},
    DEFAULT_EXECUTION_CLIENT_CONFIG_NAME_RETH: {"client": "reth"},
    DEFAULT_EXECUTION_CLIENT_CONFIG_NAME_BESU: {"client": "besu"},
    DEFAULT_EXECUTION_CLIENT_CONFIG_NAME_NETHERMIND: {"client": "nethermind"}
}

DEFAULT_CONSENSUS_CONFIG_FIELDS = [
    "launcher",
    "num-validators",
    "log-level",
    "p2p-port",
    "beacon-api-port",
    "beacon-rpc-port",
    "beacon-metric-port",
    "validator-rpc-port",
    "validator-metric-port"
]

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
    "p2p-port": DEFAULT_CONSENSUS_P2P_PORT,
    "beacon-api-port": DEFAULT_CONSENSUS_BEACON_API_PORT,
    "beacon-rpc-port": DEFAULT_CONSENSUS_BEACON_RPC_PORT,
    "beacon-metric-port": DEFAULT_CONSENSUS_BEACON_METRIC_PORT,
    "validator-rpc-port": DEFAULT_CONSENSUS_VALIDATOR_RPC_PORT,
    "validator-metric-port": DEFAULT_CONSENSUS_VALIDATOR_METRIC_PORT,
    "num-validators": DEFAULT_NUM_VALIDATORS,
}

DEFAULT_CONSENSUS_CONFIG = {
    DEFAULT_CONSENSUS_CLIENT_CONFIG_NAME_PRYSM: {
        "client": "prysm",
        "num-validators": DEFAULT_NUM_VALIDATORS,
        "p2p-port": DEFAULT_CONSENSUS_P2P_PORT,
        "beacon-api-port": DEFAULT_CONSENSUS_BEACON_API_PORT,
        "beacon-rpc-port": DEFAULT_CONSENSUS_BEACON_RPC_PORT,
        "beacon-metric-port": DEFAULT_CONSENSUS_BEACON_METRIC_PORT,
        "validator-rpc-port": DEFAULT_CONSENSUS_VALIDATOR_RPC_PORT,
        "validator-metric-port": DEFAULT_CONSENSUS_VALIDATOR_METRIC_PORT,
    },
    DEFAULT_CONSENSUS_CLIENT_CONFIG_NAME_LIGHTHOUSE: {
        "client": "lighthouse",
        "num-validators": DEFAULT_NUM_VALIDATORS,
        "p2p-port": DEFAULT_CONSENSUS_P2P_PORT,
        "beacon-api-port": DEFAULT_CONSENSUS_BEACON_API_PORT,
        "beacon-rpc-port": DEFAULT_CONSENSUS_BEACON_RPC_PORT,
        "beacon-metric-port": DEFAULT_CONSENSUS_BEACON_METRIC_PORT,
        "validator-rpc-port": DEFAULT_CONSENSUS_VALIDATOR_RPC_PORT,
        "validator-metric-port": DEFAULT_CONSENSUS_VALIDATOR_METRIC_PORT,
    },
    DEFAULT_CONSENSUS_CLIENT_CONFIG_NAME_LODESTAR: {
        "client": "lodestar",
        "num-validators": DEFAULT_NUM_VALIDATORS,
        "p2p-port": DEFAULT_CONSENSUS_P2P_PORT,
        "beacon-api-port": DEFAULT_CONSENSUS_BEACON_API_PORT,
        "beacon-rpc-port": DEFAULT_CONSENSUS_BEACON_RPC_PORT,
        "beacon-metric-port": DEFAULT_CONSENSUS_BEACON_METRIC_PORT,
        "validator-rpc-port": DEFAULT_CONSENSUS_VALIDATOR_RPC_PORT,
        "validator-metric-port": DEFAULT_CONSENSUS_VALIDATOR_METRIC_PORT,
    },
    DEFAULT_CONSENSUS_CLIENT_CONFIG_NAME_NIMBUS: {
        "client": "nimbus",
        "num-validators": DEFAULT_NUM_VALIDATORS,
        "p2p-port": DEFAULT_CONSENSUS_P2P_PORT,
        "beacon-api-port": DEFAULT_CONSENSUS_BEACON_API_PORT,
        "beacon-rpc-port": DEFAULT_CONSENSUS_BEACON_RPC_PORT,
        "beacon-metric-port": DEFAULT_CONSENSUS_BEACON_METRIC_PORT,
        "validator-rpc-port": DEFAULT_CONSENSUS_VALIDATOR_RPC_PORT,
        "validator-metric-port": DEFAULT_CONSENSUS_VALIDATOR_METRIC_PORT,
    },
    DEFAULT_CONSENSUS_CLIENT_CONFIG_NAME_TEKU: {
        "client": "teku",
        "num-validators": DEFAULT_NUM_VALIDATORS,
        "p2p-port": DEFAULT_CONSENSUS_P2P_PORT,
        "beacon-api-port": DEFAULT_CONSENSUS_BEACON_API_PORT,
        "beacon-rpc-port": DEFAULT_CONSENSUS_BEACON_RPC_PORT,
        "beacon-metric-port": DEFAULT_CONSENSUS_BEACON_METRIC_PORT,
        "validator-rpc-port": DEFAULT_CONSENSUS_VALIDATOR_RPC_PORT,
        "validator-metric-port": DEFAULT_CONSENSUS_VALIDATOR_METRIC_PORT,
    }
}

DEFAULT_ETB_BOOTSTRAPPER_INSTANCE_NAME = "ethereum-testnet-bootstrapper"
DEFAULT_ETB_BOOTSTRAPPER_IMAGE_NAME = "ethereum-testnet-bootstrapper"
DEFAULT_ETB_BOOTSTRAPPER_TAG_NAME = "latest"
DEFAULT_ETB_BOOTSTRAPPER_ENTRYPOINT = "/source/entrypoint.sh --bootstrap-testnet --log-level debug"
DEFAULT_ETB_BOOTSTRAPPER_IP_ADDRESS = "10.0.20.201"

DEFAULT_BOOTNODE_INSTANCE_NAME = "eth2-bootnode"
DEFAULT_BOOTNODE_IMAGE_NAME = "ethereum-testnet-bootstrapper"
DEFAULT_BOOTNODE_TAG_NAME = "latest"
DEFAULT_BOOTNODE_ENTRYPOINT = "/source/deps/launchers/bootnodes/launch-eth2-bootnode.sh"
DEFAULT_BOOTNODE_IP_ADDRESS = "10.0.20.202"

DEFAULT_NODE_WATCH_INSTANCE_NAME = "node-watch"
DEFAULT_NODE_WATCH_IMAGE_NAME = "ethereum-testnet-bootstrapper"
DEFAULT_NODE_WATCH_TAG_NAME = "latest"
DEFAULT_NODE_WATCH_ENTRYPOINT = "python3 /source/src/node_watch.py --log-level info --monitor heads:slot --monitor checkpoints:slot --max-retries 3"

DEFAULT_GENERIC_INSTANCE_NUM_NODES = 1
DEFAULT_GENERIC_INSTANCE_IMAGE = "ethereum-testnet-bootstrapper"
DEFAULT_GENERIC_INSTANCE_TAG = "latest"

REQUIRED_GENERIC_INSTANCE_FIELDS = [
    "image",
    "tag",
    "entrypoint",
]

# The bootstrapper, the CL bootnode
DEFAULT_GENERIC_INSTANCES = {
    DEFAULT_ETB_BOOTSTRAPPER_INSTANCE_NAME: {
        "image": DEFAULT_ETB_BOOTSTRAPPER_IMAGE_NAME,
        "tag": DEFAULT_ETB_BOOTSTRAPPER_TAG_NAME,
        "start-ip-address": DEFAULT_ETB_BOOTSTRAPPER_IP_ADDRESS,
        # "num-nodes": 1,
        "entrypoint": DEFAULT_ETB_BOOTSTRAPPER_ENTRYPOINT,
    },
    DEFAULT_BOOTNODE_INSTANCE_NAME: {
        "image": DEFAULT_BOOTNODE_IMAGE_NAME,
        "tag": DEFAULT_BOOTNODE_TAG_NAME,
        "start-ip-address": DEFAULT_BOOTNODE_IP_ADDRESS,
        "entrypoint": DEFAULT_BOOTNODE_ENTRYPOINT,
        # "num-nodes": 1,
        "additional-env": {
            "consensus-bootnode-start-ip-addr": "10.0.20.201",
            "consensus-bootnode-private-key": "bc971f814d7bd37f7502cc67408c4f2c5a06e1b3d48dc041e42b5478154df1a8",
            "consensus-bootnode-enr-port": 9001,
            "consensus-bootnode-api-port": 6000,
            "consensus-bootnode-enr-file": DEFAULT_CONSENSUS_BOOTNODES_FILE,
        }
    },
    DEFAULT_NODE_WATCH_INSTANCE_NAME: {
        "image": DEFAULT_NODE_WATCH_IMAGE_NAME,
        "tag": DEFAULT_NODE_WATCH_TAG_NAME,
        "entrypoint": DEFAULT_NODE_WATCH_ENTRYPOINT,
    }
}


def get_default_execution_config_value(client: str, entry: str):
    if (client, entry) in DEFAULT_EXECUTION_CLIENT_SPECIFIC_VALUES_MAP:
        return DEFAULT_EXECUTION_CLIENT_SPECIFIC_VALUES_MAP[(client, entry)]
    if entry in DEFAULT_EXECUTION_VALUES_MAP:
        return DEFAULT_EXECUTION_VALUES_MAP[entry]
    else:
        raise Exception(f"Failed to get required field: {entry} from config (execution-configs)")


def get_default_consensus_config_value(client: str, entry: str):
    if (client, entry) in DEFAULT_CONSENSUS_CLIENT_SPECIFIC_VALUES_MAP:
        return DEFAULT_CONSENSUS_CLIENT_SPECIFIC_VALUES_MAP[(client, entry)]
    if entry in DEFAULT_CONSENSUS_VALUES_MAP:
        return DEFAULT_CONSENSUS_VALUES_MAP[entry]
    else:
        raise Exception(f"Failed to get required field: {entry} from config: (consensus-configs)")
