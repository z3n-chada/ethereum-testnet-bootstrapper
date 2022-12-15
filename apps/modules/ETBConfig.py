"""
    EthereumTestnetBootstrapper Config Utils

    many config operations can be repetitive so we add these functions
    here to speed up module/app development.
"""
import logging

# from .ExecutionRPC import ExecutionClientJsonRPC
from ruamel import yaml

logger = logging.getLogger("bootstrapper_log")


class GenericConfigurationEntry(object):
    """
    A configuration entry contains config value pairs, it may
    use num-nodes and have multiptle entries, but that should
    never effect the return value for a configuration item.

    (e.g. a ConfigEntry should never have a start-ip-addr)
    """

    def __init__(self, config_entry):
        self.config = config_entry
        self.__name__ = "GenericConfigurationEntry"

    def has(self, value):
        return value in self.config

    def get(self, value):
        if value in self.config:
            return self.config[value]
        else:
            raise Exception(f"{self.__name__} has no entry: {value}")


class ConsensusConfig(GenericConfigurationEntry):
    def __init__(self, consensus_config):
        super().__init__(consensus_config)
        self.__name__ = "ConsensusConfig"


class ExecutionConfig(GenericConfigurationEntry):
    def __init__(self, execution_config):
        super().__init__(execution_config)
        self.__name__ = "ExecutionConfig"


class ConsensusBootnodeConfig(GenericConfigurationEntry):
    def __init__(self, consensus_bootnode_config):
        super().__init__(consensus_bootnode_config)
        self.__name__ = "ConsensusBootnodeConfig"


class ExecutionBootnodeConfig(GenericConfigurationEntry):
    def __init__(self, execution_bootnode_config):
        super().__init__(execution_bootnode_config)
        self.__name__ = "ExecutionBootnodeConfig"


class GenericClient(GenericConfigurationEntry):
    """
    A GenericClient is a step up form a config entry. The values that it
    stores may be influenced by the node which we are discussing.

    In the current implementation a GenericClient is one of the following:

    ConsensusClient
    ExecutionClient
    ConsensusBootnodeClient
    GenericModule (GenericClient)

    If the config value we are seeking changes based on the node which we are
    accessing (e.g. ip-address) , or the value of the config entry is derrived
    from multiple configuration values (e.g. rpc endoint = protocol://ip:port)
    this constitutes as reserved_value. When we do the lookup and access this
    entry we use get_(config_entry)(node).

    Reserved values can also be used to specify a client specific
    implemenation. For example ExecutionClient's use execution-data-dir as
    the root directory, however consensus clients use
    testnet-dir/node_X/{execution-client-name}

    GenericClients can implement all the different ConfigEntries, so their
    respective client implemenatations need to observe this.

    Lastly additional-env values that are specified must be node agnostic
    and always be returned first so values can be overwritten in the config
    with ease.
    """

    def __init__(self, name, etb_config, client_config):
        super().__init__(client_config)
        self.__name__ = "GenericClient"
        self.etb_config = etb_config
        self.name = name

        # additional env entry.
        self.additional_env = {}

        # the nested config_entries to search after all else fails.
        self.config_entries = []

        if "consensus-config" in self.config:
            self.consensus_config = self.etb_config.get_consensus_config(
                self.config["consensus-config"]
            )
            self.config_entries.append(self.consensus_config)
        else:
            self.consensus_config = None

        if "execution-config" in self.config:
            self.execution_config = self.etb_config.get_execution_config(
                self.config["execution-config"]
            )
            self.config_entries.append(self.execution_config)
        else:
            self.execution_config = None

        if "consensus-bootnode-config" in self.config:
            self.consensus_bootnode_config = (
                self.etb_config.get_consensus_bootnode_config(
                    self.config["consensus-bootnode-config"]
                )
            )
            self.config_entries.append(self.consensus_bootnode_config)
        else:
            self.consensus_bootnode_config = None

        if "execution-bootnode-config" in self.config:
            self.execution_bootnode_config = (
                self.etb_config.get_execution_bootnode_config(
                    self.config["execution-bootnode-config"]
                )
            )
            self.config_entries.append(self.execution_bootnode_config)
        else:
            self.execution_bootnode_config = None

        if "additional-env" in self.config:
            self.additional_env = self.config["additional-env"]

    def has(self, value):
        # currently this is broken if there is a getter, but it is not defined. workarounds here.
        if value in ["jwt-secret-file"]:
            return value in self.config

        if value in self.additional_env:
            logger.debug(f"{self.__name__}:has {value} in additional-env")
            return True

        if value in self.config:
            logger.debug(f"{self.__name__}:has {value} in config")
            return True

        if hasattr(self, f'get_{value.replace("-","_")}'):
            logger.debug(f"{self.__name__}:has custom getter for {value}")
            return True

        if hasattr(self, f'{value.replace("-","_")}'):
            logger.debug(f"{self.__name__}:hasattr for {value}")
            return True

        for config_entry in self.config_entries:
            if config_entry.has(value):
                logger.debug(
                    f"{self.__name__}:has config entry {config_entry} with {value}"
                )
                return True
        # lastly check the main etb-config
        if self.etb_config.has(value):
            logger.debug(f"{self.__name__}:has found {value} in etb_config")
            return True

    def custom_get(self, value, node=None):

        return None

    def get(self, value, node=None):
        """
        Find and return the value which you seek. Values may be stored
        in the following, ordered by priority.

        1. additional-env
        2. (special client dependent values) overridden in the client object.
        3. the local objects get_{value}(node) function.
        4. its config
        5. one of its associated config entries
        6. the root etb_config object.

        """
        if not self.has(value):
            raise Exception(
                f"{self.__name__}:requested value: {value} it doesn't have. "
            )

        if isinstance(node, int):
            if node > self.get("num-nodes"):
                raise Exception(
                    f"{self.__name__} requested value with node > num-nodes"
                )
        if value in self.additional_env:
            return self.additional_env[value]

        if self.custom_get(value, node) is not None:
            return self.custom_get(value, node)

        if hasattr(self, f"get_{value.replace('-','_')}"):
            return getattr(self, f"get_{value.replace('-','_')}")(node)

        if hasattr(self, f"{value.replace('-','_')}"):
            return getattr(self, f"{value.replace('-','_')}")

        if value in self.config:
            return self.config[value]

        for config_entry in self.config_entries:
            if config_entry.has(value):
                return config_entry.get(value)

        # we couldn't find a client implementation check the etb-config object.
        # this will raise an exception if it not found.

        return self.etb_config.get(value)

    def get_ip_addr(self, node):
        prefix = ".".join(self.config["start-ip-addr"].split(".")[:3]) + "."
        base = int(self.config["start-ip-addr"].split(".")[-1])
        return prefix + str(base + int(node))

    def get_ip_addrs(self):
        return [self.get_ip_addr(node) for node in range(self.num_nodes)]

    def get_netrestrict_range(self, unused=""):
        return self.etb_config.get("netrestrict-range")

    def get_graffiti(self, node):
        if "graffiti" in self.config:
            return f'{self.config["graffiti"]}-{node}'
        else:
            return f"{self.name}-{node}-graffiti"

    def get_execution_http_endpoint(self, node):
        ip = self.get("ip-addr", node)
        port = self.get("execution-http-port")
        return f"http://{ip}:{port}"

    def get_ws_web3_ip_addr(self, node):
        # if we have our one local one, use it. else check the local config
        if "ws-web3-ip-addr" in self.config:
            return self.config["ws-web3-ip-addr"]

        if self.has_local_exectuion_client:
            return "127.0.0.1"

        raise Exception(
            f"{self.__name__} is requesting execution endpoint but does "
            + "not have a local one, or a config entry for ws-web3-ip-addr"
        )

    def get_http_web3_ip_addr(self, node):
        # if we have our one local one, use it. else check the local config
        if "http-web3-ip-addr" in self.config:
            return self.config["http-web3-ip-addr"]

        if self.has_local_exectuion_client:
            return "127.0.0.1"

        raise Exception(
            f"{self.__name__} is requesting execution endpoint but does "
            + "not have a local one, or a config entry for "
            + "http-web3-ip-addr"
        )

    def get_jwt_secret_file(self, node):
        return f"{self.config['jwt-secret-file']}-{node}"

    def get_execution_bootnode(self, node):
        bootnodes = self.etb_config.get("execution-bootnodes")
        for name, bn in bootnodes.items():
            bootnode_enode = bn.get("execution-bootnode-enode")
            bootnode_ip = bn.get_ip_addr(0)  # only one client per bootnode
            bootnode_disc_port = self.get("execution-p2p-port")
            return f"{bootnode_enode}@{bootnode_ip}:{bootnode_disc_port}"


class ConsensusBootnodeClient(GenericClient):
    def __init__(self, name, etb_config, bootnode_config):
        super().__init__(name, etb_config, bootnode_config)
        self.__name__ = "ConsensusBootnodeClient"


class ExecutionBootnodeClient(GenericClient):
    def __init__(self, name, etb_config, bootnode_config):
        super().__init__(name, etb_config, bootnode_config)
        self.__name__ = "ExecutionBootnodeClient"
        for name, ec in self.etb_config.get("execution-clients").items():
            if name == self.get("execution-client"):
                self.execution_client = ec

    # wrapper to pull ip address from the referenced el client
    def get_ip_addr(self, node):
        return self.execution_client.get("ip-addr", node)


class ConsensusClient(GenericClient):
    """
    Consensus client as used in the config.

    May contain an execution client.
    """

    def __init__(self, name, etb_config, consensus_client_config):
        super().__init__(name, etb_config, consensus_client_config)
        self.__name__ = "ConsensusClient"
        # common attributes
        if "local-execution-client" in self.config:
            self.has_local_exectuion_client = self.config["local-execution-client"]
        else:
            self.has_local_exectuion_client = False

    def get_node_dir(self, node):
        return f"{self.get('testnet-dir')}/node_{node}"

    def get_execution_data_dir(self, node):
        return f'{self.get_node_dir(node)}/{self.execution_config.get("client")}'

    def get_consensus_target_peers(self, unused=""):
        return self.etb_config.get("num-beacon-nodes") - 1

    # returns list of results for all nodes
    def get_beacon_rpc_endpoints(self):
        port = self.ccc["beacon-api-port"]
        return [f"http://{ip}:{port}" for ip in self.get_ip_addrs()]


class ExecutionClient(GenericClient):
    def __init__(self, name, etb_config, execution_config):
        super().__init__(name, etb_config, execution_config)
        self.__name__ = "ExecutionClient"

    # differentiates itself from the consensus client.
    def get_execution_data_dir(self, node):
        return self.config["execution-data-dir"]


class ETBConfig(GenericConfigurationEntry):
    def __init__(self, path, name="ethereum-testnet-bootstrapper-config"):
        self.path = path
        self.name = name
        with open(path, "r") as f:
            self.config = yaml.safe_load(f.read())

        super().__init__(self.config)
        self.__name__ = "ETBConfig"

        self.get_value_paths = {
            "files": [
                "testnet-root",
                "geth-genesis-file",
                "erigon-genesis-file",
                "besu-genesis-file",
                "nether-mind-genesis-file",
                "consensus-config-file",
                "consensus-genesis-file",
                "testnet-dir",
                "execution-bootstrap-dir",
                "etb-config-file",
                "docker-compose-file",
                "consensus-checkpoint-file",
                "execution-checkpoint-file",
                "execution-enode-file",
            ],
            "docker": ["network-name", "ip-subnet", "volumes"],
            "config-params": ["deposit-contract-address"],
            "config-params:execution-layer": [
                "seconds-per-eth1-block",
                "execution-genesis-delay",
                "chain-id",
                "network-id",
                "merge-fork-block",
                "terminal-total-difficulty",
                "terminal-block-hash",
                "terminal-bloch-hash-activation-epoch",
                "execution-bootstrapper",
            ],
            "config-params:consensus-layer": [
                "consensus-genesis-delay",
                "preset-base",
                "min-genesis-active-validator-count",
                "eth1-follow-distance",
            ],
            "config-params:consensus-layer:forks": [
                "genesis-fork-version",
                "genesis-fork-name",
                "end-fork-name",
                "phase0-fork-version",
                "phase0-fork-epoch",
                "altair-fork-version",
                "altair-fork-epoch",
                "bellatrix-fork-version",
                "bellatrix-fork-epoch",
                "sharding-fork-version",
                "sharding-fork-epoch",
            ],
            "accounts": [
                "eth1-account-mnemonic",
                "eth1-passphrase",
                "eth1-premine",
                "validator-mnemonic",
                "withdrawl-mnemonic",
            ],
        }

    # ETB config gets are more complicated override the method.
    # node will never be used
    def has(self, value, node=None):

        if hasattr(self, f'get_{value.replace("-","_")}'):
            return True

        for nested_path in self.get_value_paths:
            full_path = nested_path.split(":")
            destination = self.config
            for p in full_path:
                destination = destination[p]
            if value in destination:
                return True

        # lastly check the local config for non-listed updates
        if value in self.config:
            logger.debug(f"ETBConfig has from local overloaded value: {value}")
            return True

    def get(self, value, node=None):

        if not self.has(value, node):
            raise Exception(f"{self.__name__}: has no value: {value}")

        if hasattr(self, f'get_{value.replace("-","_")}'):
            return getattr(self, f'get_{value.replace("-","_")}')()

        for nested_path in self.get_value_paths:
            full_path = nested_path.split(":")
            destination = self.config
            for p in full_path:
                destination = destination[p]
            if value in destination:
                return destination[value]

        # lastly check the local config for non-listed updates
        if value in self.config:
            return self.config[value]

        raise Exception(f"{self.__name__} failed to get {value} that we have")

    def get_all_clients(self):
        all_clients = {}
        # consensus clients
        for name, client in self.get_consensus_clients():
            all_clients[name] = client
        # execution clients
        for name, client in self.get_execution_clients():
            all_clients[name] = client

        return all_clients

    def get_consensus_clients(self):
        clients = {}
        # get the consensus clients.
        for name, cc in self.config["consensus-clients"].items():
            client = ConsensusClient(name, self, cc)
            clients[name] = client

        return clients

    def get_execution_clients(self):
        clients = {}
        # get the consensus clients.
        for name, ec in self.config["execution-clients"].items():
            client = ExecutionClient(name, self, ec)
            clients[name] = client

        return clients

    def get_all_execution_clients(self):
        clients = {}
        # get the consensus clients.
        for name, ec in self.config["execution-clients"].items():
            client = ExecutionClient(name, self, ec)
            clients[name] = client

        for name, cc in self.get("consensus-clients").items():
            if cc.has("has-local-exectuion-client"):
                clients[name] = ExecutionClient(
                    name,
                    self,
                    self.config["consensus-clients"][name],
                )

        return clients

    def get_generic_modules(self):
        clients = {}
        # get the consensus clients.
        for name, gm in self.config["generic-modules"].items():
            client = ExecutionClient(name, self, gm)
            clients[name] = client

        return clients

    def get_consensus_bootnodes(self):
        clients = {}
        for name, cb in self.config["consensus-bootnodes"].items():
            client = GenericClient(name, self, cb)
            clients[name] = client

        return clients

    def get_execution_bootnodes(self):
        clients = {}
        for name, eb in self.config["execution-bootnodes"].items():
            client = ExecutionBootnodeClient(name, self, eb)
            clients[name] = client

        return clients

    def get_consensus_config(self, name):
        if name not in self.config["consensus-configs"]:
            raise Exception(f"no consensus-config: {name}")
        return ConsensusConfig(self.config["consensus-configs"][name])

    def get_execution_config(self, name):
        if name not in self.config["execution-configs"]:
            raise Exception(f"no execution-config: {name}")
        return ExecutionConfig(self.config["execution-configs"][name])

    def get_consensus_bootnode_config(self, name):
        if name not in self.config["consensus-bootnode-configs"]:
            raise Exception(f"no consensus-bootnode-config: {name}")
        return ConsensusBootnodeConfig(self.config["consensus-bootnode-configs"][name])

    def get_execution_bootnode_config(self, name):
        if name not in self.config["execution-bootnode-configs"]:
            raise Exception(f"no execution-bootnode-config: {name}")
        return ExecutionBootnodeConfig(self.config["execution-bootnode-configs"][name])

    def get_testnet_bootstrapper(self):
        clients = {}
        for name, bs in self.config["testnet-bootstrapper"].items():
            client = GenericClient(name, self, bs)
            clients[name] = client
        return clients

    def get_num_beacon_nodes(self):
        num_nodes = 0
        for c in self.get_consensus_clients().values():
            num_nodes += c.get("num-nodes")
        return num_nodes

    def get_consensus_client(self, name):
        if name not in self.config["consensus-clients"]:
            raise Exception(f"no consensus client: {name}")
        return ConsensusClient(name, self, self.config["execution-clients"][name])

    def get_execution_client(self, *args):
        if name not in self.config["execution-clients"]:
            raise Exception(f"no execution client: {name}")
        return ExecutionClient(name, self, self.config["execution-clients"][name])

    def get_netrestrict_range(self):
        return self.config["docker"]["ip-subnet"]

    def get_all_clients_with_execution_clients(self):
        all_clients = self.get_execution_clients()
        consensus_clients = self.get_consensus_clients()
        for name, client in consensus_clients.items():
            if client.execution_config is not None:
                all_clients[name] = client

        for name, client in self.get_generic_modules().items():
            if client.execution_config is not None:
                all_clients[name] = client

        return all_clients

    def get_premine_keys(self):
        from web3.auto import w3

        w3.eth.account.enable_unaudited_hdwallet_features()

        mnemonic = self.get("eth1-account-mnemonic")
        passphrase = self.get("eth1-passphrase")
        premines = self.get("eth1-premine")

        keys = {}
        for acc in premines:
            acct = w3.eth.account.from_mnemonic(
                mnemonic, account_path=acc, passphrase=passphrase
            )
            pub = acct.address
            priv = acct.privateKey.hex()
            keys[pub] = priv

        return keys


if __name__ == "__main__":
    c = ETBConfig("configs/mainnet/testing.yaml")
    c._get_docker_services()
    ccs = c.get_consensus_clients()
    print(ccs)
    print(c.get_num_beacon_nodes())
    for client in ccs.values():
        print(client.serialize_to_docker_services())
