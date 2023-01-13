from enum import Enum

from ruamel import yaml
from typing import List, Dict, Union, Optional, Any
"""
    Performs the heavy lifting of parsing and consuming configs for ETB.
"""

class ForkVersion(Enum):
    Phase0 = 0
    Altair = 1
    Bellatrix = 2
    Capella = 3

class ConfigEntry(object):
    """
    A generic configuration entry which has some useful features for getting
    information out of etb-config sections.

    A ConfigEntry in the etb-config file is the root in the yaml. e.g.
    ConfigEntryName:
        {
            ConfigEntry
        }
    """

    def __init__(self, config_entry: Dict):
        if not isinstance(config_entry, ConfigEntry):
            self.config = {}
            self._validate_and_parse(config_entry)
            if "additional-env" in config_entry:
                self.config["additional-env"] = config_entry["additional-env"]

    def _validate_and_parse(self, entry):
        for k, v in entry.items():
            if k != "additional-env":
                if k in self.config.keys():
                    print(f"found duplicate {k}")
                    print(f"current key_list:{self.config.keys()}")
                    raise Exception(f"Duplicate key {k} found in {self.config.keys()} already.")
                else:
                    self.config[k] = v
                    if isinstance(v, dict):
                        self._validate_and_parse(v)
        return True

    def has(self, key):
        return key in self.config

    def get(self, key):
        if self.has(key):
            return self.config[key]
        else:
            raise Exception(f"Entry has no config entry: {key}")

    def items(self):
        return self.config.items()

    def keys(self):
        return self.config.keys()


class ModuledConfigEntry(object):
    """
    A module that encapsulates a config entry. The two differences between a
    regular config entry and a module is:
        1. It becomes one or more docker containers
        2. It specifies num-nodes

    The number of nodes refers to the number of modules, which in turn
    determines the number of docker containers for that ModuledConfigEntry.

    MODULETYPE:
        {
            ModuledConfigEntry {
                        ConfigEntry
                        num-nodes: #
            }
        }
    """

    def __init__(self, name: str, module_type: str, etb_config):
        self.name: str = name
        self.etb_config = etb_config
        self.module_type: str = module_type
        self.config: ConfigEntry = self._fetch_config_entry()

        self.defined_env_vars: List[str] = [
            "ip-address",
            "node-num",
        ]

    def __iter__(self):
        for x in range(0, self.config.get('num-nodes')):
            yield Module(self, x)

    def _fetch_config_entry(self) -> ConfigEntry:
        return ConfigEntry(self.etb_config.global_config[self.module_type][self.name])

    def has(self, key: str) -> bool:

        if hasattr(self, f"get_{key.replace('-', '_')}"):
            return True

        return self.config.has(key)

    def get(self, key: str, ndx=None):

        if key in self.__dict__:
            return self.__dict__[key]

        if hasattr(self, f"get_{key.replace('-', '_')}"):
            if ndx is None:
                return getattr(self, f'get_{key.replace("-", "_")}')()
            else:
                # some values depend on what number node we are using.
                return getattr(self, f'get_{key.replace("-", "_")}')(ndx)

        if self.config.has(key):
            return self.config.get(key)

        raise Exception(f"GenericInstance {self} can't get {key}")


class Module(ModuledConfigEntry):
    """
        One instance of a ModuledConfigEntry
    """

    def __init__(self, parent_module: ModuledConfigEntry, ndx: int):
        self.root_name = parent_module.name
        super().__init__(parent_module.name, parent_module.module_type, parent_module.etb_config)
        # overwrite the name
        self.name = f"{parent_module.name}-{ndx}"
        self.ndx = ndx
        # Modules must define their base docker vars.
        self.docker_entry: DockerEntry = DockerEntry(self)
        # defined_env_var -> DOCKER_ENV_VAR

    def _fetch_config_entry(self) -> ConfigEntry:
        # we need to override due to naming convention
        return ConfigEntry(self.etb_config.global_config[self.module_type][self.root_name])

    def has(self, key: str) -> bool:
        if hasattr(self, f"get_{key.replace('-', '_')}"):
            return True

        return self.config.has(key)

    def get(self, key: str):
        if hasattr(self, f"get_{key.replace('-', '_')}"):
            return getattr(self, f'get_{key.replace("-", "_")}')()

        if self.config.has(key):
            return self.config.get(key)

        if self.config.has('additional-env'):
            if key in self.config.get('additional-env').keys():
                return self.config.get('additional-env')[key]

        raise Exception(f"Module {self} can't get {key}")

    def get_ip_address(self) -> str:
        prefix = ".".join(self.config.get("start-ip-addr").split(".")[:3]) + "."
        base = int(self.config.get("start-ip-addr").split(".")[-1])
        return prefix + str(base + int(self.ndx))

    def get_node_num(self) -> int:
        return self.ndx

    def get_env_vars(self) -> Dict[str, Union[str, int, float]]:
        env_vars = {}
        for var in self.defined_env_vars:
            env_vars[var.replace('-', '_').upper()] = self.get(var)
        # add any env_vars from the additional env section.
        if self.has('additional-env'):
            for k, v in self.get('additional-env').items():
                env_vars[k.replace('-', '_').upper()] = v

        return env_vars


class ETBClient(ModuledConfigEntry):
    """
    A special purpose ETBClient represents an entry in the ETB config for
    one or more clients. These clients consist of both a CL and EL client.
    """

    def __init__(self, name: str, module_type: str, etb_config):
        super().__init__(name, module_type, etb_config)
        self.consensus_config: ConfigEntry = self.etb_config.consensus_configs[self.config.get('consensus-config')]
        self.execution_config: ConfigEntry = self.etb_config.execution_configs[self.config.get('execution-config')]

    def __iter__(self):
        for x in range(self.get('num-nodes')):
            yield Client(self, x)

class Client(Module, ETBClient):
    """
    An ETB client is a single client, inherit from this for either a CL or EL
    client.
    """

    def __init__(self, parent_module: ETBClient, ndx: int):
        super().__init__(parent_module, ndx)

        client_env_vars = [
            "testnet-dir",
            "jwt-secret-file",
        ]

        for env_var in client_env_vars:
            self.defined_env_vars.append(env_var)

    def __repr__(self):
        return f"[Client]:{self.name} - {self.ndx}\n"

    def get_execution_client_view(self):
        """Return an ExecutionClient view."""
        return ExecutionClient(self, self.ndx)

    def get_consensus_client_view(self):
        """Return a ConsensusClient view."""
        return ConsensusClient(self, self.ndx)

    def get_node_dir(self) -> str:
        root = self.config.get('testnet-dir')
        return f"{root}/node_{self.ndx}"

    def get_jwt_secret_file(self) -> str:
        """The path not the file."""
        return f"{self.config.get('jwt-secret-file')}-{self.ndx}"

    def get_entrypoint(self) -> str:
        return f"/bin/sh -c"

    def get_command(self) -> List:
        # to launch both scripts.
        return [f"{self.get('execution-launcher')} & {self.get('consensus-launcher')}"]


class ExecutionClient(Client):
    """
    A ExecutionClient is the CL portion of a single instance of an Client.
    It contains all the information about the CL client and its configuration
    settings.

    Requires: name, ETBClients config, ndx (which instance this belongs to.)
    """

    def __init__(self, parent_module: Client, ndx: int):
        self.parent_module = parent_module  # inheritance is misleading. it is the same instance.
        super().__init__(parent_module, ndx)
        self.name = parent_module.name
        self.root_name = parent_module.root_name

        # execution client env-vars
        execution_client_env_vars = [
            "execution-client",
            "execution-launcher",
            "execution-genesis-file",
        ]
        execution_config_env_vars = [
            "execution-log-level",
            "execution-http-apis",
            "execution-ws-apis",
            "execution-http-port",
            "execution-ws-port",
            "execution-engine-http-port",
            "execution-engine-ws-port",
            "execution-p2p-port",
            "execution-metric-port",
        ]

        execution_derived_env_vars = [
            "execution-node-dir"
        ]

        for env_var in execution_client_env_vars:
            self.defined_env_vars.append(env_var)
        for env_var in execution_config_env_vars:
            self.defined_env_vars.append(env_var)
        for env_var in execution_derived_env_vars:
            self.defined_env_vars.append(env_var)

    def has(self, key:str) -> bool:
        if hasattr(self, f"get_{key.replace('-', '_')}"):
            return True

        if self.config.has(key):
            return True

        if self.execution_config.has(key):
            return True
    def get(self, key: str):

        if hasattr(self, f"get_{key.replace('-', '_')}"):
            return getattr(self, f'get_{key.replace("-", "_")}')()

        if self.config.has(key):
            return self.config.get(key)

        if self.execution_config.has(key):
            return self.execution_config.get(key)

        raise Exception(f"Module {self} can't get {key}")

    def _fetch_config_entry(self) -> ConfigEntry:
        return self.parent_module.config

    def get_execution_genesis_file(self) -> str:
        return self.etb_config.get(f"{self.get('execution-client')}-genesis-file")

    def get_execution_node_dir(self) -> str:
        return f"{self.parent_module.get('node-dir')}/{self.get('execution-client')}"

    def get_rpc_path(self, protocol="http") -> str:
        """
            Get a path for accessing the RPC interface in
            {protocol}://{IP}:{PORT} form.
            defaults to http.
        """
        if not self.has(f"execution-{protocol}-port"):
            raise Exception(f"Couldn't look up protocol {protocol} port. Check config for execution-{protocol}-port")

        protocol_port = self.get(f"execution-{protocol}-port")
        return f"{protocol}://{self.get('ip-address')}:{protocol_port}"

class ConsensusClient(Client):
    """
    A ConsensusClient is the CL portion of a single instance of an Client.
    It contains all the information about the CL client and its configuration
    settings.
    """

    def __init__(self, parent_module: Client, ndx: int):
        self.parent_module = parent_module  # inheritance is misleading. it is the same instance.
        super().__init__(parent_module, ndx)
        self.name = parent_module.name
        self.root_name = parent_module.root_name

        # consensus client env-vars
        consensus_client_env_vars = [
            "consensus-client",
            "consensus-launcher",
            "consensus-config-file",
            "consensus-genesis-file",
        ]
        # consensus-config
        consensus_config_env_vars = [
            "consensus-num-validators",
            "consensus-p2p-port",
            "consensus-beacon-rpc-port",
            "consensus-beacon-api-port",
            "consensus-beacon-metric-port",
            "consensus-validator-rpc-port",
            "consensus-validator-metric-port",
        ]
        # derived env-vars
        derived_env_vars = [
            "consensus-node-dir",
            "consensus-graffiti",
        ]

        for env_var in consensus_client_env_vars:
            self.defined_env_vars.append(env_var)
        for env_var in consensus_config_env_vars:
            self.defined_env_vars.append(env_var)
        for env_var in derived_env_vars:
            self.defined_env_vars.append(env_var)

    def get(self, key: str):
        if hasattr(self, f"get_{key.replace('-', '_')}"):
            return getattr(self, f'get_{key.replace("-", "_")}')()

        if self.config.has(key):
            return self.config.get(key)

        if self.consensus_config.has(key):
            return self.consensus_config.get(key)

        raise Exception(f"Module {self} can't get {key}")

    def get_consensus_config_file(self) -> str:
        # the config.yaml is placed in the testnet-dir
        return f"{self.parent_module.get('testnet-dir')}/config.yaml"

    def get_consensus_genesis_file(self) -> str:
        # the config.yaml is placed in the testnet-dir
        return f"{self.parent_module.get('testnet-dir')}/genesis.ssz"

    def get_consensus_node_dir(self) -> str:
        return self.get_node_dir()

    def get_consensus_graffiti(self) -> str:
        return f"{self.get('consensus-client')}:{self.get('execution-client')}:{self.get('ip-address')}"

    def get_consensus_num_validators(self) -> int:
        return self.get('num-validators')

    def get_beacon_api_path(self) -> str:
        return f"http://{self.get('ip-address')}:{self.get('consensus-beacon-api-port')}"
    def _fetch_config_entry(self) -> ConfigEntry:
        return self.parent_module.config


class ETBConfig(object):
    """
    The overall ETBConfig class for consuming and parsing the config files used
    in ethereum-testnet-bootstrapper

    An etb config consists of the following parts:
        docker
        files
        config-params
            execution-layer
            consensus-layer
            accounts
        execution-configs
        consensus-configs
        clients
        generic-modules
    """

    def __init__(self, path):
        self.path: str = path
        self.global_config: Dict = {}

        with open(path, "r") as f:
            self.global_config = yaml.safe_load(f.read())

        self.docker: ConfigEntry = ConfigEntry(self.global_config["docker"])
        self.files: ConfigEntry = ConfigEntry(self.global_config["files"])
        self.config_params: ConfigEntry = ConfigEntry(self.global_config["config-params"])
        self.accounts: ConfigEntry = ConfigEntry(self.global_config["accounts"])

        self.execution_configs: Dict[str, ConfigEntry] = {}
        self.consensus_configs: Dict[str, ConfigEntry] = {}
        self.clients: Dict[str, ETBClient] = {}
        self.generic_modules: Dict[str, ModuledConfigEntry] = {}

        for k, v in self.global_config["execution-configs"].items():
            self.execution_configs[k] = ConfigEntry(v)
        for k, v in self.global_config["consensus-configs"].items():
            self.consensus_configs[k] = ConfigEntry(v)
        for k in self.global_config["client-modules"].keys():
            self.clients[k] = ETBClient(k, "client-modules", self)
        for k in self.global_config["generic-modules"].keys():
            self.generic_modules[k] = ModuledConfigEntry(k, "generic-modules", self)

        # ensure we have unique keys for the clients as well
        intersect = set(self.files.keys() & \
                        self.config_params.keys() & \
                        self.accounts.keys() & \
                        self.execution_configs.keys() & \
                        self.consensus_configs.keys() & \
                        self.clients.keys() & \
                        self.generic_modules.keys())

        if len(intersect) > 0:
            raise Exception("Duplicate key entries in etb-config.")

        # env vars for docker-template from the etb-config
        self.defined_env_vars = [
            "consensus-checkpoint-file",
            "execution-checkpoint-file",
            "consensus-bootnode-checkpoint-file",
            "etb-config-checkpoint-file",
            "ip-subnet",
            "consensus-bootnode-file",
            "num-client-nodes",
        ]

        config_param_vars = [
            "network-id",
            "chain-id",
        ]

        for cpv in config_param_vars:
            self.defined_env_vars.append(cpv)

    def has(self, key):

        return self.files.has(key) or \
            self.config_params.has(key) or \
            self.accounts.has(key) or \
            key in self.execution_configs or \
            key in self.consensus_configs or \
            key in self.clients or \
            key in self.generic_modules

    def get(self, key) -> Any:

        if hasattr(self, f"get_{key.replace('-', '_')}"):
            return getattr(self, f'get_{key.replace("-", "_")}')()

        if self.files.has(key):
            return self.files.get(key)

        if self.config_params.has(key):
            return self.config_params.get(key)

        if self.accounts.has(key):
            return self.accounts.get(key)

        if self.docker.has(key):
            return self.docker.get(key)

        # TODO: find a place to put the genesis time.
        # hacky workaround for now.
        if key in self.global_config:
            return self.global_config[key]

        raise Exception(f"Unhandled get {key} request on ETBConfig")

    def _get_env_vars(self) -> Dict[str, Union[str, int, float]]:
        env_vars = {}
        for var in self.defined_env_vars:
            env_vars[var.replace('-', '_').upper()] = self.get(var)
        return env_vars

    def get_clients(self) -> Dict[str, ETBClient]:
        return self.clients

    def get_generic_modules(self) -> Dict[str, ModuledConfigEntry]:
        return self.generic_modules

    def get_execution_rpc_paths(self, protocol='http') -> Dict[str, str]:
        """
            Return the rpc path in str form of all the execution clients
            listed in the config.

            protocol: defaults to http.
            returns: Dict[name, rpc_path]
        """
        named_rpc_dict = {}
        for client_module in self.get_clients().values():
            for client_instance in client_module:
                el_view = client_instance.get_execution_client_view()
                rpc_path = el_view.get_rpc_path(protocol)
                named_rpc_dict[client_instance.name] = rpc_path

        return named_rpc_dict

    def get_all_consensus_client_beacon_api_paths(self) -> Dict[str, str]:

        api_paths: Dict[str, str] = {}

        for client_modules in self.clients.values():
            for client_instance in client_modules:
                cl_view = client_instance.get_consensus_client_view()
                api_paths[client_instance.name] = cl_view.get('beacon-api-path')

        return api_paths

    def get_all_execution_clients_and_apis(self, protocol='http') -> Dict[str, List[str]]:
        """
            Get all the execution clients and their el-apis they implement.
            all apis are cast to lowercase.
        """
        client_api_listings: Dict[str, List[str]] = {}
        "hello"
        for client_modules in self.clients.values():
            for client_instance in client_modules:
                apis: List[str] = []
                el_view = client_instance.get_execution_client_view()
                for api in el_view.get('execution-http-apis').split(','):
                    apis.append(api.lower())
                client_api_listings[client_instance.name] = apis

        return client_api_listings

    def get_num_client_nodes(self) -> int:
        num_nodes = 0
        for client_module in self.clients.values():
            num_nodes += client_module.get('num-nodes')
        return num_nodes

    def get_genesis_fork(self) -> ForkVersion:
        if self.get('capella-fork-epoch') == 0:
            return ForkVersion.Capella

        if self.get('bellatrix-fork-epoch') == 0:
            return ForkVersion.Bellatrix

        if self.get('altair-fork-epoch') == 0:
            return ForkVersion.Altair

        return ForkVersion.Phase0

    def get_genesis_fork_version(self) -> int:
        lookup_dict = {
            ForkVersion.Phase0 : self.get('phase0-fork-version'),
            ForkVersion.Altair : self.get('altair-fork-version'),
            ForkVersion.Bellatrix : self.get('bellatrix-fork-version'),
            ForkVersion.Capella : self.get('capella-fork-version'),
        }
        return lookup_dict[self.get_genesis_fork()]

    def get_final_fork(self) -> ForkVersion:
        '''The last fork in the config that is not in far-future'''
        far_future_epoch = 18446744073709551615
        if self.get('capella-fork-epoch') != far_future_epoch:
            return ForkVersion.Capella

        if self.get('bellatrix-fork-epoch') != far_future_epoch:
            return ForkVersion.Bellatrix

        if self.get('altair-fork-epoch') != far_future_epoch:
            return ForkVersion.Altair

        return ForkVersion.Phase0

    def get_seconds_per_cl_block(self) -> int:
        return 12

    def get_consensus_blocks_per_epoch(self) -> int:
        return 32
    def get_consensus_genesis_delay(self) -> int:
        # how long before testnet genesis that cl genesis occurs in seconds
        return self.get('eth1-follow-distance') * self.get('seconds-per-eth1-block') + self.get('execution-genesis'
                                                                                                '-delay')

    def get_clique_signers(self, num_signers=1) -> List[str]:
        """
        In order of premines we allocate those to signers
        :param num_signers:
        :return: List[signer1,signer2,...]
        """
        from web3.auto import w3
        w3.eth.account.enable_unaudited_hdwallet_features()

        pub_keys = []
        premines = [x for x in self.global_config['accounts']['eth1-premine']]

        for x in range(num_signers):
            acct = w3.eth.account.from_mnemonic(self.get("eth1-account-mnemonic"), account_path=premines[x], passphrase=self.get("eth1-passphrase"))
            pub_keys.append(acct.address)

        return pub_keys

    def set_genesis_time(self, t: int) -> None:
        """Set the genesis time in the etb-config"""
        self.global_config["bootstrap-genesis"] = t

    def write_config_to_file(self, new_file_path: str = None):
        """write the config out to the expected path. We do this so we can
           update values during the bootstrap process. It uses the file found
           in the config by default."""

        path_to_use: str = self.get('etb-config-file')
        if new_file_path is not None:
            path_to_use = new_file_path

        with open(path_to_use, "w") as f:
            yaml.safe_dump(self.global_config, f)

    def write_checkpoint_file(self, checkpoint: str):
        if checkpoint not in self.files.keys():
            raise Exception("Tried to write undefined checkpoint")

        with open(self.files.get(checkpoint), "w") as checkpoint_file:
            checkpoint_file.write("1")

    def write_to_docker_compose(self, path: str=None):
        """
            Write a docker-compose with all the clients and generic modules
            from the config to the specified path. It defaults to whats given
            in the config file.
        """
        p = self.get('docker-compose-file')
        if path is not None:
            p = path
        with open(p, "w") as f:
            f.write(yaml.safe_dump(self._get_docker_repr()))

    def _get_docker_repr(self) -> dict:

        services = {}
        # clients
        for client_module in self.clients.values():
            env_vars = self._get_env_vars()
            for client in client_module:
                for client_env_key, client_env_value in client.get('env-vars').items():
                    env_vars[client_env_key] = client_env_value
                for cl_key, cl_value in client.get('consensus-client-view').get('env-vars').items():
                    env_vars[cl_key] = cl_value
                for el_key, el_value in client.get('execution-client-view').get('env-vars').items():
                    env_vars[el_key] = el_value
                docker_entry = client.docker_entry
                docker_entry.environment = env_vars
                services[client.name] = docker_entry.serialize_docker_entry()

        # generic modules
        for gm in self.generic_modules.values():
            env_vars = self._get_env_vars()
            for gm_instance in gm:
                for gm_env_key, gm_env_value in gm_instance.get_env_vars().items():
                    env_vars[gm_env_key] = gm_env_value
                docker_entry = gm_instance.docker_entry
                docker_entry.environment = env_vars
                services[gm_instance.name] = docker_entry.serialize_docker_entry()

        return {"services": services,
                "networks": {
                    self.get("network-name"): {
                        "driver": "bridge",
                        "ipam": {"config": [{"subnet": self.get('ip-subnet')}]}
                    }
                },
                }


"""
    Classes to facilitate transforming the etb-config file to other formats and
    specifications.
"""


class DockerEntry(object):
    """
    A docker entry is all the information required by a docker-template file
    to bring up all the instances. A docker entry represents one unique
    instance.

    Typical Docker Entry:

    """

    def __init__(self, module: Module):
        self.module = module
        self.container_name = self.module.get('container-name')
        self.image = self.module.get('image')
        if self.module.has('tag'):
            self.tag = self.module.get('tag')
        else:
            self.tag = "latest"
        self.entrypoint = self.module.get('entrypoint')
        self.ip_address = self.module.get('ip-address')
        self.network_name = self.module.etb_config.docker.get('network-name')
        self.volumes = self.module.etb_config.docker.get('volumes')
        self.environment = self.module.get('env-vars')
        if self.module.has('command'):
            self.command = self.module.get('command')
        else:
            self.command = None

    def serialize_docker_entry(self) -> dict:
        entry = {
            "container_name": self.container_name,
            "entrypoint": self.entrypoint.split(),
            "environment": self.environment,
            "image": f"{self.image}:{self.tag}",
            "volumes": self.volumes,
            "networks": {self.network_name: {"ipv4_address": self.ip_address}}
        }
        if self.command is not None:
            entry["command"] = self.command
        return entry


if __name__ == "__main__":
    config = ETBConfig("../../configs/mainnet/geth-post-merge-genesis.yaml")
    # for k, v in config.get_all_execution_clients_and_apis().items():
    #     if 'admin' in v:
    #         print(k)
    # for multi_clients in config.get_clients().values():
    #     for client in multi_clients:
    #         print(type(client))
    #         print(client)
    #         print(client.consensus_config)
    #         print(client.docker_entry.serialize_docker_entry())

    # print(config._get_docker_repr())
    # print(config._get_env_vars())
    # for generic_module in config.generic_modules.values():
    #     for instance in generic_module:
    #         print(instance.get_env_vars())
    # for client_modules in config.clients.values():
    #     for instance in client_modules:
    #         print(instance.get_env_vars())
    #         el_view = instance.get('execution-client-view')
    #         print(el_view.get_env_vars())
    #         cl_view = instance.get('consensus-client-view')
    #         print(cl_view)
    #         print(cl_view.get_env_vars())
    #         print(cli)
    # config.write_to_docker_template("../../docker-compose.yaml")
    # print(config._get_docker_repr())
    prysm_module = config.get_clients()['prysm-geth']
    # print(prysm_module.get('validator-password'))
    print(prysm_module.config.config['additional-env']['validator-password'])

    print(config.get_clique_signers())



