"""
    EthereumTestnetBootstrapper Config Utils

    many config operations can be repetitive so we add these functions
    here to speed up module/app development.
"""
from .ExecutionRPC import ExecutionClientJsonRPC
from ruamel import yaml


class GenericConfigurationEntry(object):
    def __init__(self, config_entry):
        self.config = config_entry
        self.reserved_values = []

    def has(self, value):
        if value in self.reserved_values:
            return True
        return value in self.config

    def get(self, value):
        if value in self.reserved_values:
            if hasattr(self, f"get_{value}"):
                return getattr(self, f"get_{value}")()
            else:
                raise Exception(
                    f"{self.__name__}: getter for reserved entry: {value} not implemented."
                )

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


class ConsensusBootnodeConfig(GenericConfigurationEntry):
    def __init__(self, consensus_bootnode_config):
        super().__init__(consensus_bootnode_config)


class GenericClient(GenericConfigurationEntry):
    """
    Main class that has basic information about a client, be it exectuion,
    consensus, bootnode, or a generic module.
    """

    def __init__(self, name, etb_config, client_config):
        super().__init__(client_config)
        self.etb_config = etb_config
        self.name = name
        self.num_nodes = self.config["num-nodes"]

        self.reserved_buckets = []
        rv = ["ip-addr", "consensus-target-peers", "netrestrict-range", "graffiti"]
        for v in rv:
            self.reserved_values.append(v)

        self.additional_env = {}

        if "consensus-config" in self.config:
            self.consensus_config = self.etb_config.get_consensus_config(
                self.config["consensus-config"]
            )
            self.reserved_buckets.append(self.consensus_config)
        else:
            self.consensus_config = None

        if "execution-config" in self.config:
            self.execution_config = self.etb_config.get_execution_config(
                self.config["execution-config"]
            )
            self.reserved_buckets.append(self.execution_config)
        else:
            self.execution_config = None

        if "consensus-bootnode-config" in self.config:
            self.consensus_bootnode_config = (
                self.etb_config.get_consensus_bootnode_config(
                    self.config["consensus-bootnode-config"]
                )
            )
            self.reserved_buckets.append(self.consensus_bootnode_config)
        else:
            self.consensus_bootnode_config = None

        if "additional-env" in self.config:
            self.additional_env = self.config["additional-env"]

    def has(self, value):
        if value in self.reserved_values:
            return True

        if value in self.config:
            return True

        for bucket in self.reserved_buckets:
            if bucket.has(value):
                return True
        # lastly check the main etb-config
        if self.etb_config.has(value):
            return True

        if value in self.additional_env:
            return True

    def get(self, value, node=None):
        # additional-env trumps all
        if value in self.additional_env:
            return self.additional_env[value]
        # tha case where we don't need to do a calculation.
        if node is None:
            # the value doesn't depend on which node we are asking about.
            if value in self.reserved_values:
                if hasattr(self, f"get_{value.replace('-','_')}"):
                    return getattr(self, f"get_{value.replace('-','_')}")()
                else:
                    raise Exception(
                        f"{self.__name__}: getter for reserved entry: {value} not implemented."
                    )
            # the value is in a nested configuration.
            for bucket in self.reserved_buckets:
                if bucket.has(value):
                    print(f"self.__name__: get() returning {value} from {bucket}")
                    return bucket.get(value)

            if value in self.config:
                return self.config[value]

            # lastly check the root configuation (geneis files, terminal-total-difficulty etc
            if self.etb_config.has(value):
                return self.etb_config.get(value)

            raise Exception(f"{self.__name__} has no entry: {value}")

        else:
            if value in self.reserved_values:
                if hasattr(self, f"get_{value.replace('-','_')}"):
                    return getattr(self, f"get_{value.replace('-','_')}")(node)

                raise Exception(
                    f"{self.__name__}: get with non-none node failed to get {value} for {node}"
                )
            # value is in a bucket.
            for bucket in self.reserved_buckets:
                if bucket.has(value):
                    print(f"self.__name__: get() returning {value} from {bucket}")
                    return bucket.get(value)

            # lastly check our own store, in case node was passed by accident.
            if value in self.config:
                return self.config[value]

            if self.etb_config.has(value):
                return self.etb_config.get(value)

            else:
                raise Exception(f"{self.__name__} has no entry: {value}")

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


class ConsensusBootnodeClient(GenericClient):
    def __init__(self, name, etb_config, bootnode_config):
        super().__init__(name, etb_config, bootnode_config)


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

        rv = ["node-dir", "execution-data-dir"]
        for v in rv:
            self.reserved_values.append(v)

    # single client queries must supply node
    def get_node_dir(self, node):
        return f"{self.get('testnet-dir')}/node_{node}"

    def get_execution_data_dir(self, node):
        return f'{self.get_node_dir(node)}/{self.execution_config.get("client")}'

    # def get_ws_web3_ip_addr(self, unused=""):
    #    if "ws-web3-ip-addr" in self.cc:
    #        return self.cc["ws-web3-ip-addr"]
    #    elif "ws-web3-ip-addr" in self.ccc:
    #        return self.ccc["ws-web3-ip-addr"]
    #    elif self.has_local_exectuion_client:
    #        return "127.0.0.1"
    #    else:
    #        raise Exception(f"Could not get ws-web3-ip-addr for {self.name}")

    # def get_http_web3_ip_addr(self, unused=""):
    #    if "http-web3-ip-addr" in self.cc:
    #        return self.cc["http-web3-ip-addr"]
    #    elif "http-web3-ip-addr" in self.ccc:
    #        return self.ccc["http-web3-ip-addr"]
    #    elif self.has_local_exectuion_client:
    #        return "127.0.0.1"
    #    else:
    #        raise Exception(f"Could not get http-web3-ip-addr for {self.name}")

    def get_consensus_target_peers(self, unused=""):
        return self.etb_config.get("num-beacon-nodes") - 1

    # returns list of results for all nodes
    def get_beacon_rpc_endpoints(self):
        port = self.ccc["beacon-api-port"]
        return [f"http://{ip}:{port}" for ip in self.get_ip_addrs()]

    def get_ip_addrs(self):
        return [self.get_ip_addr(node) for node in range(self.num_nodes)]

    # use this method to create a dict of services to append to a docker-compose.yaml


class ExecutionClient(GenericClient):
    def __init__(self, name, etb_config, execution_config):
        super().__init__(name, etb_config, execution_config)
        rv = ["execution-data-dir"]
        for v in rv:
            self.reserved_values.append(v)

    def get_execution_http_endpoint(self, node):
        return f"{self.get_ip_addr(node)}:{self.get_execution_http_port()}"

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

        rv = ["num-beacon-nodes", "execution-bootstrapper-client", "netrestrict-range"]
        for v in rv:
            self.reserved_values.append(v)

        self.get_value_paths = {
            "files": [
                "testnet-root",
                "geth-genesis-file",
                "besu-genesis-file",
                "nethermind-genesis-file",
                "consensus-config-file",
                "consensus-genesis-file",
                "testnet-dir",
                "execution-bootstrap-dir",
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
            "config-params:execution-layer:clique": [
                "clique-enabled",
                "clique-signers",
                "clique-epoch",
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

        if value in self.reserved_values:
            return True

        for nested_path in self.get_value_paths:
            full_path = nested_path.split(":")
            destination = self.config
            for p in full_path:
                destination = destination[p]
            if value in destination:
                return True

    def get(self, value, node=None):

        if not self.has(value, node):
            raise Exception(f"{self.__name__}: has no value: {value}")

        if value in self.reserved_values:
            if hasattr(self, f"get_{value.replace('-','_')}"):
                return getattr(self, f"get_{value.replace('-','_')}")()
            else:
                raise Exception(
                    f"{self.__name__}: getter for reserved entry: {value.replace('-','_')} not implemented."
                )

        for nested_path in self.get_value_paths:
            full_path = nested_path.split(":")
            destination = self.config
            for p in full_path:
                destination = destination[p]
            if value in destination:
                return destination[value]

        raise Exception(f"{self.__name__} failed to get {value} that we have")

    def get_consensus_clients(self):
        clients = {}
        # get the consensus clients.
        for cc in self.config["consensus-clients"]:
            client = ConsensusClient(cc, self, self.config["consensus-clients"][cc])
            clients[cc] = client

        return clients

    def get_execution_clients(self):
        clients = {}
        # get the consensus clients.
        for name, ec in self.config["execution-clients"].items():
            client = ExecutionClient(name, self, ec)
            clients[name] = client

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

    def get_testnet_bootstrapper(self):
        clients = {}
        for name, bs in self.config["testnet-bootstrapper"].items():
            client = GenericClient(name, self, bs)
            clients[name] = client
        return clients

    def get_num_beacon_nodes(self):
        num_nodes = 0
        for c in self.get_consensus_clients().values():
            num_nodes += c.num_nodes
        return num_nodes

    def get_consensus_client(self, name):
        if name not in self.config["consensus-clients"]:
            raise Exception(f"no consensus client: {name}")
        return ConsensusClient(name, self, self.config["execution-clients"][name])

    def get_execution_client(self, name):
        if name not in self.config["execution-clients"]:
            raise Exception(f"no execution client: {name}")
        return ExecutionClient(name, self, self.config["execution-clients"][name])

    def get_execution_bootstrapper_client(self):
        bootstrapper_name = self.get("execution-bootstrapper")
        print("returning execution client")
        return self.get_execution_client(bootstrapper_name)

    def get_netrestrict_range(self):
        return self.config["docker"]["ip-subnet"]

    # def get_preset_base(self):
    #    return self.c["config-params"]["consensus-layer"]["preset-base"]

    # def get_start_fork(self):
    #    return self.c["config-params"]["consensus-layer"]["forks"]["genesis-fork-name"]

    # def get_end_fork(self):
    #    return self.c["config-params"]["consensus-layer"]["forks"]["end-fork-name"]

    # def get_consensus_genesis_delay(self):
    #    return self.config_params["consensus-layer"]["genesis-delay"]

    # def get_min_genesis_active_validator_count(self):
    #    return self.config_params["consensus-layer"][
    #        "min-genesis-active-validator-count"
    #    ]

    # def get_deposit_contract_address(self):
    #    return self.config_params["deposit-contract-address"]

    # def get_seconds_per_eth1_block(self):
    #    return self.config_params["execution-layer"]["seconds-per-eth1-block"]

    # def get_terminaltotaldifficulty(self):
    #    return self.config_params["execution-layer"]["terminal-total-difficulty"]

    # def get_chain_id(self):
    #    return self.config_params["execution-layer"]["chain-id"]

    # def get_network_id(self):
    #    return self.config_params["execution-layer"]["network-id"]

    # def get_genesis_fork_name(self):
    #    return self.config_params["consensus-layer"]["forks"]["genesis-fork-name"]

    # def get_genesis_fork_version(self):
    #    return self.config_params["consensus-layer"]["forks"]["genesis-fork-version"]

    # def get_altair_fork_version(self):
    #    return self.config_params["consensus-layer"]["forks"]["altair-fork-version"]

    # def get_altair_fork_epoch(self):
    #    return self.config_params["consensus-layer"]["forks"]["altair-fork-epoch"]

    # def get_bellatrix_fork_version(self):
    #    return self.config_params["consensus-layer"]["forks"]["bellatrix-fork-version"]

    # def get_bellatrix_fork_epoch(self):
    #    return self.config_params["consensus-layer"]["forks"]["bellatrix-fork-epoch"]

    # def get_sharding_fork_version(self):
    #    return self.config_params["consensus-layer"]["forks"]["sharding-fork-version"]

    # def get_sharding_fork_epoch(self):
    #    return self.config_params["consensus-layer"]["forks"]["sharding-fork-epoch"]

    # def get_terminal_block_hash(self):
    #    return self.config_params["execution-layer"]["terminal-block-hash"]

    # def get_terminal_block_hash_activation_epoch(self):
    #    return self.config_params["execution-layer"][
    #        "terminal-block-hash-activation-epoch"
    #    ]

    # def get_geth_execution_genesis(self):
    #    return self.files["geth-genesis"]

    # def get_besu_execution_genesis(self):
    #    return self.files["besu-genesis"]

    # def get_nethermind_execution_genesis(self):
    #    return self.files["nethermind-genesis"]

    # def get_execution_client_http_rpc_endpoint(
    #    self, client_name, node, timeout=5, non_error=True
    # ):
    #    # TODO: add logic for exceptions on a bad node (more than num_nodes)
    #    if client_name in self.execution_clients:
    #        ec = ExecutionClient(client_name, self, self.execution_clients[client_name])
    #        ip = ec.get_ip_addr(node)
    #        port = ec.get_execution_http_port()
    #    elif client_name in self.consensus_clients:
    #        cc = ConsensusClient(client_name, self, self.consensus_clients[client_name])
    #        if cc.has_local_exectuion_client:
    #            ip = cc.get_ip_addr(node)
    #            port = cc.get_execution_http_port()
    #    else:
    #        raise Exception("Could not find client {client_name}")

    #    return ExecutionClientJsonRPC(
    #        f"http://{ip}:{port}", timeout=timeout, non_error=non_error
    #    )


if __name__ == "__main__":
    c = ETBConfig("configs/mainnet/testing.yaml")
    c._get_docker_services()
    ccs = c.get_consensus_clients()
    print(ccs)
    print(c.get_num_beacon_nodes())
    for client in ccs.values():
        print(client.serialize_to_docker_services())
