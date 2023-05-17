import logging
import pathlib
import re

from .Consensus import DEFINED_CONSENSUS_FORK_NAMES, ConsensusFork
from .ETBConstants import (
    PresetEnum,
    MinimalPreset,
    MainnetPreset,
    ForkVersion,
    always_match_regex,
    Epoch,
    TotalDifficultyStep,
    PresetOverrides,
)
from ruamel import yaml
from typing import List, Dict, Union, Any, Generator, Type
from web3.auto import w3


class PremineKeyPair(object):
    """
    Represents the premines used in genesis.
    """

    def __init__(self, premine_path: str, password: str, mnemonic: str):
        self.mnemonic = mnemonic
        self.password = password
        self.premine_path = premine_path
        self._init()

    def _init(self):
        w3.eth.account.enable_unaudited_hdwallet_features()

        acct = w3.eth.account.from_mnemonic(
            self.mnemonic, account_path=self.premine_path, passphrase=self.password
        )
        self.public_key = acct.address
        self.private_key = acct.key.hex()


"""
    Performs the heavy lifting of parsing and consuming configs for ETB.
"""


class ConfigEntry(object):
    """
    A wrapper around some entries in a config file that allows access via
    has and get to reduce boilerplate code.

    we use the recursive definition for nested fields that do *not* contain
    instances.
    """

    def __init__(self, config_key, data: dict, recursive=False):
        self.config_key = config_key
        self.invalid_keys = []
        self.required_keys = []
        self.ignored_keys = []
        self.config_entry = {}
        if recursive:
            self._validate_and_populate(data)
        else:
            self.config_entry = self._validate_and_parse(data)

    def _validate_and_parse(self, config_entry: dict) -> dict:
        """
        Ensures the data contained in this config follows spec.
        :return: the entry.
        """
        entry = {}
        for k, v in config_entry.items():
            if k in self.invalid_keys:
                raise Exception(f"Invalid entry {k} in config-entry")
            elif k not in self.ignored_keys:

                entry[k] = config_entry[k]
                # do it recursively
            else:
                pass
        missing_keys = [k for k in self.required_keys if k not in entry]
        if len(missing_keys) != 0:
            raise Exception(f"{type(self).__name__} does not contain all required keys: {', '.join(missing_keys)}")
        return entry

    # recursive entries
    def _validate_and_populate(self, config_entry: dict):
        bad_keys = ["image", "additional-env"]  # make sure this is not an instance
        for k, v in config_entry.items():
            if k in bad_keys:
                raise Exception("Cannot recursive config entry setup for Instances.")
            if k in self.config_entry.keys():
                print(f"found duplicate {k}")
                print(f"current key_list:{self.config_entry.keys()}")
                raise Exception(
                    f"Duplicate key {k} found in {self.config_entry.keys()} already."
                )
            else:
                self.config_entry[k] = v
                if isinstance(v, dict):
                    self._validate_and_populate(v)

    def has(self, key):
        # first check for overloaded getters.
        if hasattr(self, f"get_{key.replace('-', '_')}"):
            return True

        # now check the config entry
        if key in self.config_entry:
            return True

        # last check if the dict of the object itself.
        return key in self.__dict__

    def get(self, key):

        if hasattr(self, f"get_{key.replace('-', '_')}"):
            return getattr(self, f'get_{key.replace("-", "_")}')()

        elif key in self.config_entry.keys():
            return self.config_entry[key]

        # last check for the dict
        if key in self.__dict__:
            return self.__dict__[key]

        else:
            raise Exception(f"Entry has no config entry: {key}")

    def items(self):
        return self.config_entry.items()

    def keys(self):
        return self.config_entry.keys()


class ConsensusConfigEntry(ConfigEntry):
    def __init__(self, data: dict):
        self.required_keys = [
            "client",
            "launcher",
            "log-level",
            "num-validators",
            "p2p-port",
            "beacon-api-port",
            "beacon-rpc-port",
            "validator-rpc-port",
            "beacon-metric-port",
            "validator-metric-port",
        ]
        self.invalid_keys = []
        self.ignored_keys = []
        self.config_entry = super()._validate_and_parse(data)


class ExecutionConfigEntry(ConfigEntry):
    def __init__(self, data: dict):
        self.required_keys = [
            "client",
            "launcher",
            "log-level",
            "http-apis",
            "http-port",
            "ws-port",
            "ws-apis",
            "engine-http-port",
            "engine-ws-port",
            "metric-port",
        ]
        self.invalid_keys = []
        self.ignored_keys = []
        self.config_entry = super()._validate_and_parse(data)


class Instance(ConfigEntry):
    """
    Contains a representation of a docker container that will be running
    in the local testnet.
    """

    def __init__(self, root_name: str, ndx: int, config: dict):
        self.config_entry = config
        self.root_name = root_name
        self.name = f"{root_name}-{ndx}"
        self.ndx = ndx

        # environment variables that need to be populated in docker container
        self.defined_env_vars = ["ip-address"]

    def get_ip_address(self) -> str:
        prefix = (
            ".".join(self.config_entry.get("start-ip-address").split(".")[:3]) + "."
        )
        base = int(self.config_entry.get("start-ip-address").split(".")[-1])
        return prefix + str(base + int(self.ndx))

    def get_env_vars(self) -> Dict[str, Union[str, int, float]]:
        env_vars = {}
        for var in self.defined_env_vars:
            env_vars[var.replace("-", "_").upper()] = self.get(var)
        # add any env_vars from the additional env section.
        if self.has("additional-env"):
            for k, v in self.get("additional-env").items():
                env_vars[k.replace("-", "_").upper()] = v

        return env_vars

    def get_docker_repr(self, docker_config: ConfigEntry) -> dict:
        """
        Get the docker-compose representation of this service.
        :return:
        """
        entry = {
            "container_name": self.name,
            "hostname": self.name,
            "image": f"{self.get('image')}:{self.get('tag')}",
            "volumes": docker_config.get("volumes"),
            "networks": {
                docker_config.get("network-name"): {
                    "ipv4_address": self.get_ip_address()
                }
            },
        }
        if self.has("entrypoint"):
            entry["entrypoint"] = self.get("entrypoint").split()
        else:
            entry["entrypoint"] = ["/bin/sh", "-c"]

        if self.has("docker-command"):
            entry["command"] = self.get("docker-command")

        env_vars = self.get_env_vars()

        if len(env_vars.keys()) > 0:
            entry["environment"] = env_vars

        return entry


class InstanceCollection(ConfigEntry):
    """
    Describes a collection of instances.
    """

    def __init__(self, name: str, entry: dict):
        # config entry code

        self.required_keys = [
            "image",
            "tag",
            "start-ip-address",
            "num-nodes",
        ]
        self.ignored_keys = [
            # 'entrypoint',  # handled in inherited classes
        ]
        self.invalid_keys = []
        self.config_entry = super()._validate_and_parse(entry)
        # instance code
        self.name = name
        self.num_nodes: int = self.config_entry.get("num-nodes")

    def __iter__(self):
        for x in range(self.get("num-nodes")):
            yield Instance(self.name, x, self.config_entry)


class ClientInstance(Instance, ConfigEntry):
    """
    Represents a single instance with a CL and EL node.
    Inherits ConfigEntry for get and has abstractions
    """

    def __init__(
        self,
        root_name: str,
        ndx: int,
        config: dict,
        cl_config: ConsensusConfigEntry,
        el_config: ExecutionConfigEntry,
        files_config_entry: ConfigEntry,
    ):
        super().__init__(root_name, ndx, config)
        self.consensus_config: ConsensusConfigEntry = cl_config
        self.execution_config: ExecutionConfigEntry = el_config
        self.etb_files_config: ConfigEntry = (
            files_config_entry  # used to derive various path information.
        )

        consensus_env_vars = [
            # env vars defined in the consensus config
            "consensus-client",
            "consensus-launcher",
            "consensus-config-file",
            "consensus-genesis-file",
            "consensus-num-validators",
            "consensus-p2p-port",
            "consensus-beacon-rpc-port",
            "consensus-beacon-api-port",
            "consensus-beacon-metric-port",
            "consensus-validator-rpc-port",
            "consensus-validator-metric-port",
            "consensus-log-level",
            # env vars that are derived.
            "consensus-node-dir",
            "consensus-graffiti",
        ]

        execution_env_vars = [
            "execution-client",
            "execution-launcher",
            "execution-genesis-file",
            "execution-log-level",
            "execution-http-apis",
            "execution-ws-apis",
            "execution-http-port",
            "execution-ws-port",
            "execution-engine-http-port",
            "execution-engine-ws-port",
            "execution-p2p-port",
            "execution-metric-port",
            # env vars that are derived
            "execution-node-dir",
        ]

        shared_env_vars = [
            "jwt-secret-file",
            "testnet-dir",
        ]

        # prysm only cases
        prysm_env_vars = [
            "validator-password",
            "wallet-password-path",
        ]

        for k in consensus_env_vars:
            self.defined_env_vars.append(k)
        for k in execution_env_vars:
            self.defined_env_vars.append(k)
        for k in shared_env_vars:
            self.defined_env_vars.append(k)
        if self.get("consensus-client") == "prysm":
            for k in prysm_env_vars:
                self.defined_env_vars.append(k)

    def has(self, key):
        # first check for overloaded getters.
        if hasattr(self, f"get_{key.replace('-', '_')}"):
            return True

        # now check the config entry
        if key in self.config_entry:
            return True

        # in order to fetch the has/get from consensus and execution configs
        split_key = key.split("-")
        if split_key[0] == "consensus":
            return self.consensus_config.has("-".join(split_key[1:]))

        if split_key[0] == "execution":
            return self.execution_config.has("-".join(split_key[1:]))
        # lastly check if the dict of the object itself.
        return key in self.__dict__

    def get(self, key):

        if not self.has(key):
            raise Exception(f"Entry has no config entry: {key}")

        if hasattr(self, f"get_{key.replace('-', '_')}"):
            return getattr(self, f'get_{key.replace("-", "_")}')()

        elif key in self.config_entry.keys():
            return self.config_entry[key]

        # in order to fetch the has/get from consensus and execution configs
        split_key = key.split("-")
        if split_key[0] == "consensus":
            return self.consensus_config.get("-".join(split_key[1:]))

        if split_key[0] == "execution":
            return self.execution_config.get("-".join(split_key[1:]))

        # last check for the dict
        elif key in self.__dict__:
            return self.__dict__[key]

        else:
            raise Exception("Should not occur.")

    def get_docker_command(self) -> list:
        return [f"{self.get('execution-launcher')} & {self.get('consensus-launcher')}"]

    # generic overrides
    def get_testnet_dir(self) -> str:
        return f"{self.etb_files_config.get('testnet-dir')}/{self.root_name}"

    def get_jwt_secret_file(self) -> str:
        return f"{self.get_testnet_dir()}/jwt-secret"

    # consensus related overrides
    def get_consensus_config_file(self) -> str:
        return f"{self.get_testnet_dir()}/config.yaml"

    def get_consensus_genesis_file(self) -> str:
        return f"{self.get_testnet_dir()}/genesis.ssz"

    def get_consensus_graffiti(self) -> str:
        return f"{self.name}"

    def get_consensus_node_dir(self) -> str:
        return f"{self.etb_files_config.get('testnet-dir')}/{self.root_name}/node_{self.ndx}"

    def get_full_beacon_api_path(self) -> str:
        # Returns the full path to the clients consensus beacon api port
        return f"http://{self.get_ip_address()}:{self.get('consensus-beacon-api-port')}"

    # prysm only overrides
    def get_wallet_password_path(self) -> str:
        return f"{self.get_consensus_node_dir()}/wallet-password.txt"

    def get_validator_password(self) -> str:
        return "testnet-password"

    # execution related overrides
    def get_execution_genesis_file(self) -> str:
        if self.get("execution-client") == "nethermind":
            # be careful with the env vars.
            return self.etb_files_config.get("nether-mind-genesis-file")
        return self.etb_files_config.get(f"{self.get('execution-client')}-genesis-file")

    def get_execution_node_dir(self) -> str:
        return f"{self.get_consensus_node_dir()}/{self.get('execution-client')}"

    def get_full_execution_http_jsonrpc_path(self, protocol="http") -> str:
        # Returns the full path to the clients execution jsonrpc port
        client_req_str = f"execution-{protocol}-port"
        return f"{protocol}://{self.get_ip_address()}:{self.get(client_req_str)}"


class ClientInstanceCollection(InstanceCollection):
    def __init__(
        self,
        name: str,
        entry: dict,
        cl_config: ConsensusConfigEntry,
        el_config: ExecutionConfigEntry,
        files_config_entry: ConfigEntry,
    ):
        super().__init__(name, entry)
        self.cl_config: ConsensusConfigEntry = cl_config
        self.el_config: ExecutionConfigEntry = el_config
        self.files_config_entry: ConfigEntry = files_config_entry

    def __iter__(self) -> Generator[ClientInstance, Any, None]:
        for x in range(self.get("num-nodes")):
            yield ClientInstance(
                self.name,
                x,
                self.config_entry,
                self.cl_config,
                self.el_config,
                self.files_config_entry,
            )

    # when creating client dirs we need to know the root for the client instance dirs.
    def get_root_client_testnet_dir(self) -> str:
        return f"{self.files_config_entry.get('testnet-dir')}/{self.name}"


class ETBConfig(object):
    """
    Super Object that allows complex queries on etb-configs that
    return a variety of data and representations of data.
    """

    def __init__(self, path: str, logger: logging.Logger = None):
        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger: logging.Logger = logger

        self.global_config: dict = {}

        # parse the config file and create data structures.
        config_path = pathlib.Path(path)
        if config_path.exists():
            self.logger.debug(f"Opening etb-config file: {config_path}")
            with open(config_path, "r") as f:
                try:
                    self.global_config = yaml.safe_load(f.read())
                except Exception as e:
                    self.logger.error("Error parsing etb-config yaml.")
                    raise Exception("Unable to parse yaml file.")
        else:
            self.logger.error(f"No etb-config file in path: {path}")
            raise Exception(f"No file found at: {path}")

        self.docker: ConfigEntry = ConfigEntry("docker",
            self.global_config["docker"], recursive=True
        )
        self.files: ConfigEntry = ConfigEntry("files",
            self.global_config["files"], recursive=True
        )
        self.config_params: ConfigEntry = ConfigEntry("config-params",
            self.global_config["config-params"], recursive=True
        )
        self.accounts: ConfigEntry = ConfigEntry("accounts",
            self.global_config["accounts"], recursive=True
        )
        # when calling .get() on etb-config we iterate through these config entries.
        # ensure we do not have duplicates.
        intersection = set(
            self.docker.keys()
            & self.files.keys()
            & self.config_params.keys()
            & self.accounts.keys()
        )

        if len(intersection) > 0:
            raise Exception(
                "Duplicate key entries in etb-config across dockers, files, config-params, and accounts."
            )

        # process all the instances.
        self.consensus_configs: dict[str, ConsensusConfigEntry] = {}
        for cc, entry in self.global_config["consensus-configs"].items():
            self.consensus_configs[cc] = ConsensusConfigEntry(entry)

        self.execution_configs: dict[str, ExecutionConfigEntry] = {}
        for ec, entry in self.global_config["execution-configs"].items():
            self.execution_configs[ec] = ExecutionConfigEntry(entry)

        self.client_instance_collections: dict[str, ClientInstanceCollection] = {}
        for ci, entry in self.global_config["client-instances"].items():
            # grab the referenced consensus configs.
            cl_key = entry["consensus-config"]
            el_key = entry["execution-config"]
            if cl_key not in self.consensus_configs:
                raise Exception(
                    f"Reference to consensus config {cl_key} not in consensus-configs section."
                )
            if el_key not in self.execution_configs:
                raise Exception(
                    f"Reference to execution config {cl_key} not in execution-configs section."
                )
            cl_config = self.consensus_configs[cl_key]
            el_config = self.execution_configs[el_key]
            self.client_instance_collections[ci] = ClientInstanceCollection(
                ci, entry, cl_config, el_config, self.files
            )

        self.generic_instance_collections: dict[str, InstanceCollection] = {}
        for gi, entry in self.global_config["generic-instances"].items():
            self.generic_instance_collections[gi] = InstanceCollection(gi, entry)

        # set useful members that describe the testnet.
        self.preset_base: Type[
            Union[MainnetPreset, MinimalPreset]
        ] = self.get_preset_base()
        # in case we need to perform actions for clique network.
        self.clique_signer_instance_name: Union[None, str] = None

        # consensus forks
        self.consensus_forks: dict[str, ConsensusFork] = {}
        for fork_name in DEFINED_CONSENSUS_FORK_NAMES:
            if not self.has(f"{fork_name}-fork-version"):
                raise Exception(f"Missing {fork_name}-fork-version in config-file.")

            fork_version = self.get(f"{fork_name}-fork-version")
            fork_epoch = self.get(f"{fork_name}-fork-epoch")
            self.consensus_forks[fork_name] = ConsensusFork(fork_name, fork_version, fork_epoch)

    # define a get and has construct for ease of use in modules.
    def has(self, key) -> bool:
        exists_in_config_entries = (
            key in self.docker.keys()
            or key in self.files.keys()
            or key in self.config_params.keys()
            or key in self.accounts.keys()
        )

        if exists_in_config_entries:
            return True

        # etb-config can also be used like a ConfigEntry
        if hasattr(self, f"get_{key.replace('-', '_')}"):
            return True

        return False

    def get(self, key):
        if not self.has(key):
            raise Exception(f"etb-config doesn't have result for key: {key}")

        if hasattr(self, f"get_{key.replace('-', '_')}"):
            return getattr(self, f'get_{key.replace("-", "_")}')()

        if self.files.has(key):
            return self.files.get(key)

        if self.docker.has(key):
            return self.docker.get(key)

        if self.config_params.has(key):
            return self.config_params.get(key)

        if self.accounts.has(key):
            return self.accounts.get(key)

        raise Exception("Should not occur.")

    # get data structures describing instances running on the network
    def get_client_instances(
        self,
        client_name_filter: re.Pattern[str] = always_match_regex,
        el_api_filter: re.Pattern[str] = always_match_regex,
    ) -> List[ClientInstance]:
        possible_clients = []
        name_matched_clients = []
        el_matched_clients = []
        for collections in self.client_instance_collections.values():
            for clients in collections:
                possible_clients.append(clients)

        # for speed
        if (
            client_name_filter == always_match_regex
            and el_api_filter == always_match_regex
        ):
            return possible_clients
        else:
            for client in possible_clients:
                if client_name_filter.search(client.name) is not None:
                    name_matched_clients.append(client)
            for client in name_matched_clients:
                if el_api_filter.search(client.get("execution-http-apis")) is not None:
                    el_matched_clients.append(client)

        return el_matched_clients

    def get_generic_instances(self) -> List[Instance]:
        all_generic_instances = []
        for collections in self.generic_instance_collections.values():
            for instances in collections:
                all_generic_instances.append(instances)
        return all_generic_instances

    def get_docker_compose_repr(self) -> dict:
        """
        Takes all the information contained in the config file and flattens
        it into a suitable representation for a docker-compose file.
        :return: docker-compose compatible yaml
        """
        # env-vars that are added to every service in the docker
        global_env_vars_to_get = [
            # checkpoint files
            "etb-config-checkpoint-file",
            "consensus-checkpoint-file",
            "execution-checkpoint-file",
            "consensus-bootnode-checkpoint-file",
            "consensus-bootnode-file",
            # misc globals
            "ip-subnet",
            "num-client-nodes",
            # execution vars only contained in etb-config
            "chain-id",
            "network-id",
        ]

        global_env_vars = {}
        for var in global_env_vars_to_get:
            global_env_vars[var.replace("-", "_").upper()] = self.get(var)

        services = {}
        for generic_instances in self.get_generic_instances():
            services[generic_instances.name] = generic_instances.get_docker_repr(
                self.docker
            )
            for k, v in global_env_vars.items():
                services[generic_instances.name]["environment"][k] = v

        for client_instances in self.get_client_instances():
            services[client_instances.name] = client_instances.get_docker_repr(
                self.docker
            )
            for k, v in global_env_vars.items():
                services[client_instances.name]["environment"][k] = v

        return {
            "services": services,
            "networks": {
                self.docker.get("network-name"): {
                    "driver": "bridge",
                    "ipam": {"config": [{"subnet": self.docker.get("ip-subnet")}]},
                }
            },
        }

    # get information about the testnet
    def get_preset_base(self) -> Type[Union[MainnetPreset, MinimalPreset]]:
        preset_base = self.config_params.get("preset-base")
        if preset_base == "minimal":
            return MinimalPreset
        if preset_base == "mainnet":
            return MainnetPreset

        raise Exception("Invalid preset-base in consensus config-parameters.")

    def get_preset_value(self, str_repr: str) -> int:
        """
            Get the value of a preset. Some can be overwritten, so check
            those first before returning the defaul.
        :param str_repr: preset variable
        :return: int(value)
        """
        sanitized_input = str_repr.replace("_", "-").lower()
        defined_lookups = {
            "slots-per-epoch": self.preset_base.SLOTS_PER_EPOCH,
            "epochs-per-eth1-voting-period": self.preset_base.EPOCHS_PER_ETH1_VOTING_PERIOD,
            "seconds-per-slot": self.preset_base.SECONDS_PER_SLOT,
            "seconds-per-eth1-block": self.preset_base.SECONDS_PER_ETH1_BLOCK,
            "min-validator-withdrawability-delay": self.preset_base.MIN_VALIDATOR_WITHDRAWABILITY_DELAY,
            "shard-committee-period": self.preset_base.SHARD_COMMITTEE_PERIOD,
            "eth1-follow-distance": self.preset_base.ETH1_FOLLOW_DISTANCE,
            "inactivity-score-bias": self.preset_base.INACTIVITY_SCORE_BIAS,
            "inactivity-score-recovery-rate": self.preset_base.INACTIVITY_SCORE_RECOVERY_RATE,
            "ejection-balance": self.preset_base.EJECTION_BALANCE,
            "min-per-epoch-churn-limit": self.preset_base.MIN_PER_EPOCH_CHURN_LIMIT,
            "churn-limit-quotient": self.preset_base.CHURN_LIMIT_QUOTIENT,
            "proposer-score-boost": self.preset_base.PROPOSER_SCORE_BOOST,
            "field-elements-per-blob": self.preset_base.FIELD_ELEMENTS_PER_BLOB,
        }

        for enum_override in PresetOverrides:
            if sanitized_input == enum_override:
                if self.config_params.has(enum_override):
                    override = self.config_params.get(enum_override)
                    self.logger.debug(
                        f"Returning etb-config overwritten preset: {enum_override} : {override}"
                    )
                    return override

        if sanitized_input in defined_lookups:
            value = defined_lookups[sanitized_input].value
            self.logger.debug(
                f"returning default preset for {sanitized_input} : {value}"
            )
            return value

        raise Exception(f"No preset value defined for vairable: {str_repr}")

    def get_genesis_fork_upgrade(self) -> ForkVersion:
        """
        The genesis fork upgrade is the network fork on the start of the
        network. **NOT** the phase0 version used for signatures!

        This is used for the TestnetBootstrapper to identify how the network
        should come up.
        :return:
        """
        if self.get("deneb-fork-epoch") == 0:
            return ForkVersion.Deneb
        if self.get("capella-fork-epoch") == 0:
            return ForkVersion.Capella
        if self.get("bellatrix-fork-epoch") == 0:
            return ForkVersion.Bellatrix
        if self.get("altair-fork-epoch") == 0:
            return ForkVersion.Altair
        if self.get("phase0-fork-epoch") == 0:
            return ForkVersion.Phase0
        else:
            raise Exception("No genesis-fork-epoch set to 0.")

    def get_consensus_genesis_delay(self) -> int:
        """
        Calculate the consensus genesis delay.
        If we aren't doing a bellatrix genesis then we use eth1-follow-distance
        :return: int(delay)
        """
        if self.get_genesis_fork_upgrade() < ForkVersion.Bellatrix:
            return self.get_preset_value(
                "eth1-follow-distance"
            ) * self.get_preset_value("seconds-per-eth1-block")
        else:
            return 0

    def get_execution_merge_fork_block(self) -> int:
        """
        Based on the configuration parameters for fork version epochs
        calculate the merge fork block height for the execution layer
        :return: block height as int.
        """
        # post-merge genesis
        if self.get_genesis_fork_upgrade() >= ForkVersion.Bellatrix:
            return 0

        # determine if we are doing a merge
        if self.config_params.get("bellatrix-fork-epoch") == Epoch.FarFuture.value():
            return Epoch.FarFuture.value()

        # pre bellatrix genesis with configured merge.
        merge_slot = (
            self.config_params.get("bellatrix-fork-epoch")
            * self.preset_base.SLOTS_PER_EPOCH.value
        )
        merge_time = (
            merge_slot * self.preset_base.SECONDS_PER_SLOT.value
        ) + self.get_consensus_genesis_delay()
        merge_el_block = int(merge_time // self.get("seconds-per-eth1-block"))

        self.logger.debug(f"time to merge: {merge_time} -> eth1-block {merge_el_block}")
        return merge_el_block

    def get_consensus_fork_delay_seconds(self, fork_name) -> int:
        """
        Given a consensus fork calculate the time that it will occur relative
        to the genesis of the beacon chain.
        """
        if fork_name not in self.consensus_forks.keys():
            raise Exception(f"Fork {fork_name}  not defined in config. {fork_name}")

        consensus_fork = self.consensus_forks[fork_name]
        return (
            consensus_fork.epoch
            * self.preset_base.SLOTS_PER_EPOCH.value
            * self.preset_base.SECONDS_PER_SLOT.value
        ) + self.get_consensus_genesis_delay()


    def get_bootstrap_genesis_time(self) -> int:
        if "bootstrap-genesis" in self.global_config:
            return self.global_config["bootstrap-genesis"]

        raise Exception("Tried getting bootstrap genesis before bootstrapping.")

    def get_shanghai_time(self) -> int:
        """
        the ELs have shangaiTime which should correspond with CAPELLA_FORK_EPOCH
        :return: shanghaiTime
        """
        capella_fork_epoch = self.config_params.get("capella-fork-epoch")
        capella_delta = (
            capella_fork_epoch
            * self.preset_base.SLOTS_PER_EPOCH.value
            * self.preset_base.SECONDS_PER_SLOT.value
        ) + self.get_consensus_genesis_delay()
        shanghai_time = self.get_bootstrap_genesis_time() + capella_delta
        self.logger.debug(
            f"Calculated shanghai time as cl epoch: {capella_fork_epoch} at time: {shanghai_time}"
        )
        return shanghai_time

    def get_terminal_total_difficulty(self) -> int:
        """
        The chain total difficulty at the time of the bellatrix upgrade
        :return: int(TTD)
        """
        ttd = self.get_execution_merge_fork_block() * TotalDifficultyStep.Clique.value
        self.logger.debug(f"Calculate TTD: {ttd}")
        return ttd

    def get_num_client_nodes(self) -> int:
        return len(self.get_client_instances())

    def get_premine_keypairs(self) -> list[PremineKeyPair]:

        """
        Returns a dict with eth1 premind keys: {pubkey: privkey}
        :return: {premine : (public, private)}
        """
        pkps = []
        for acc in self.accounts.get("eth1-premine"):
            pkp = PremineKeyPair(
                acc,
                self.accounts.get("eth1-passphrase"),
                self.accounts.get("eth1-account-mnemonic"),
            )
            pkps.append(pkp)

        return pkps

    def get_number_of_unaccounted_validator_deposits(self) -> int:
        """
        Returns the number of validator deposits that are not accounted for in the genesis state.
        :return: int
        """
        total_validator_count = 0
        for client in self.get_client_instances():
            client_validator_count = client.consensus_config.get("num-validators")
            total_validator_count += client_validator_count
        self.logger.debug(f"total client validator indexes: {total_validator_count}")
        return total_validator_count - self.config_params.get(
            "min-genesis-active-validator-count"
        )

    # setters for modifying the etb-config file exposed to nodes.
    def set_bootstrap_genesis_time(self, bootstrap_genesis_time: int):
        self.global_config["bootstrap-genesis"] = bootstrap_genesis_time

    # save off information about the etb-config file.
    def write_etb_config_to_testnet_dir(self):
        """
        Write the etb-config file with all the modified fields to testnet dir.
        This allows other modules to use the same parameters from the bootstrapper.
        :return:
        """
        with open(self.files.get("etb-config-file"), "w") as f:
            self.logger.debug(
                f"Dumping etb-config global_config to file: {self.files.get('etb-config-file')}"
            )
            yaml.safe_dump(self.global_config, f)

    # quick conversions
    def epoch_to_slot(self, epoch: int):
        """epoch -> slot"""
        return epoch * self.preset_base.SLOTS_PER_EPOCH.value
