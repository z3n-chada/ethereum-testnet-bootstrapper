import json
import logging
import pathlib
import time
from typing import List, Union

from pydantic.utils import deep_update
from ruamel import yaml

from .defaults import DEFAULT_GENERIC_INSTANCE_NUM_NODES, DEFAULT_DOCKER_CONFIG, DEFAULT_FILES_CONFIG, \
    DEFAULT_EXECUTION_CONFIG, DEFAULT_EXECUTION_CONFIG_FIELDS, get_default_execution_config_value, \
    DEFAULT_CONSENSUS_CONFIG, DEFAULT_CONSENSUS_CONFIG_FIELDS, get_default_consensus_config_value, \
    DEFAULT_GENERIC_INSTANCES, REQUIRED_GENERIC_INSTANCE_FIELDS, DEFAULT_GENERIC_INSTANCE_IMAGE, \
    DEFAULT_GENERIC_INSTANCE_TAG, DEFAULT_MINIMAL_DOCKER_TAG, DEFAULT_MAINNET_DOCKER_TAG, DEFAULT_MINIMAL_DOCKER_IMAGE, \
    DEFAULT_MAINNET_DOCKER_IMAGE, DEFAULT_CONSENSUS_CLIENT_INSTANCE_ADDITIONAL_ENV, DEFAULT_TESTNET_CONFIG
from ..common.consensus import ConsensusFork, TerminalBlockHash
from ..common.consensus import (
    PresetEnum,
    MinimalPreset,
    MainnetPreset,
    ForkVersionName,
    Epoch,
)
# make it easier to read the output etb-config.yaml file.
yaml.SafeDumper.ignore_aliases = lambda *args : True

def _set_default(config: dict, entry: str, default_param):
    """
    @param config: Config to read from
    @param entry: The entry to look up
    @param default_param: The default param to use
    @return:
    """
    # if its defined use it
    if entry in config:
        return config[entry]
    else:
        return default_param


class Config:
    """Represents a config object.

    The only difference between this and a regular object is the easy
    mapping of fields that use hyphens v.s. underscores.
    """

    def __init__(self, name: str):
        self.name: str = name
        # fields that get flattened.
        self.fields: list[str] = []

    def __contains__(self, item):
        return hasattr(self, item.replace("-", "_"))

    def __getitem__(self, item: str):
        return getattr(self, item.replace("-", "_"))

    def __setitem__(self, key, value):
        setattr(self, key.replace("-", "_"), value)


class DockerConfig(Config):
    """The docker config specified in etb. This is used to construct the
    docker-compose.yaml.

    This is found in ETBCOnfig -> docker
    The required fields are:
        - network-name: the name of the docker network to use/create
        - ip-subnet: the ip-subnet of the testnet

    The implicit fields are:
        - volumes: the volumes to mount in the docker-compose file
            ['./data:/data', './:/source/']
    """

    def __init__(self, config: dict):
        super().__init__("docker-config")

        required_fields = ["network-name", "ip-subnet"]

        for k in required_fields:
            if k not in config:
                raise ValueError(f"docker-config is missing required field {k}")

        self.network_name: str = config["network-name"]
        self.ip_subnet: str = config["ip-subnet"]
        self.volumes: List[str] = ["./data:/data", "./:/source/"]


class FilesConfig(Config):
    """Files used in the ETBConfig. These are implicit and not specified in the
    ETBConfig file.

    Files specified in the ETBConfig are added to this object as well.
    """

    def __init__(self, optional_overrides=None, is_deneb_experiment=False):
        super().__init__("files")

        self.is_deneb_experiment = is_deneb_experiment
        self.optional_overrides = {}
        if optional_overrides is None:
            optional_overrides = {}

        fields = {
            "testnet-root": "/data/",
            "geth-genesis-file": "/data/geth-genesis.json",
            "besu-genesis-file": "/data/besu-genesis.json",
            "nether-mind-genesis-file": "/data/nethermind-genesis.json",
            "consensus-config-file": "/data/config.yaml",
            "consensus-genesis-file": "/data/genesis.ssz",
            "consensus-bootnode-file": "/data/consensus-bootnodes.txt",
            "etb-config-file": "/data/etb-config.yaml",
            "local-testnet-dir": "/data/local-testnet/",
            "docker-compose-file": "/source/docker-compose.yaml",  # used by host so use /source/
            "etb-config-checkpoint-file": "/data/etb-config-checkpoint.txt",
            "consensus-checkpoint-file": "/data/consensus-checkpoint.txt",
            "execution-checkpoint-file": "/data/execution-checkpoint.txt",
            "consensus-bootnode-checkpoint-file": "/data/consensus-bootnode-checkpoint.txt",
            "deposit-contract-deployment-block-hash-file": "/data/deposit-contract-deployment-block-hash.txt",
            "deposit-contract-deployment-block-number-file": "/data/deposit-contract-deployment-block-number.txt",
        }

        deneb_only_fields = {
            "trusted-setup-txt-file": "/data/trusted-setup.txt",
            "trusted-setup-json-file": "/data/trusted-setup.json",
        }

        # el genesis files
        self.geth_genesis_file: pathlib.Path = pathlib.Path(fields["geth-genesis-file"])
        self.besu_genesis_file: pathlib.Path = pathlib.Path(fields["besu-genesis-file"])
        self.nether_mind_genesis_file: pathlib.Path = pathlib.Path(
            fields["nether-mind-genesis-file"]
        )
        # consensus genesis files
        self.consensus_config_file: pathlib.Path = pathlib.Path(
            fields["consensus-config-file"]
        )
        self.consensus_genesis_file: pathlib.Path = pathlib.Path(
            fields["consensus-genesis-file"]
        )
        # consensus bootnode files
        self.consensus_bootnode_file: pathlib.Path = pathlib.Path(
            fields["consensus-bootnode-file"]
        )
        # etb specific files
        self.etb_config_file: pathlib.Path = pathlib.Path(fields["etb-config-file"])
        self.testnet_root: pathlib.Path = pathlib.Path(fields["testnet-root"])
        self.local_testnet_dir: pathlib.Path = pathlib.Path(fields["local-testnet-dir"])
        self.docker_compose_file: pathlib.Path = pathlib.Path(
            fields["docker-compose-file"]
        )
        # checkpoint files
        self.etb_config_checkpoint_file: pathlib.Path = pathlib.Path(
            fields["etb-config-checkpoint-file"]
        )
        self.consensus_checkpoint_file: pathlib.Path = pathlib.Path(
            fields["consensus-checkpoint-file"]
        )
        self.execution_checkpoint_file: pathlib.Path = pathlib.Path(
            fields["execution-checkpoint-file"]
        )
        self.consensus_bootnode_checkpoint_file: pathlib.Path = pathlib.Path(
            fields["consensus-bootnode-checkpoint-file"]
        )
        # deposit contract deployment files
        self.deposit_contract_deployment_block_hash_file: pathlib.Path = pathlib.Path(
            fields["deposit-contract" "-deployment-block-hash" "-file"]
        )
        self.deposit_contract_deployment_block_number_file: pathlib.Path = pathlib.Path(
            fields["deposit-contract" "-deployment-block" "-number-file"]
        )

        if is_deneb_experiment:
            self.trusted_setup_txt_file: pathlib.Path = pathlib.Path(
                deneb_only_fields["trusted-setup-txt-file"]
            )
            self.trusted_setup_json_file: pathlib.Path = pathlib.Path(
                deneb_only_fields["trusted-setup-json-file"]
            )

        # add optional overrides
        for key, value in optional_overrides.items():
            if key not in fields:
                # add new field
                fields[key] = value
                setattr(self, key.replace("-", "_"), pathlib.Path(value))

        self.fields = fields


class TestnetConfig(Config):
    """Testnet's configuration found in ETBConfig -> testnet-config.

    testnet-config:
        execution-layer: ExecutionLayerTestnetConfig
        consensus-layer: ConsensusLayerTestnetConfig
        deposit-contract-address: [str]
    """

    def __init__(self, config: dict):
        super().__init__("testnet-config")

        self.execution_layer: ExecutionLayerTestnetConfig = ExecutionLayerTestnetConfig(
            config["execution-layer"]
        )
        self.consensus_layer: ConsensusLayerTestnetConfig = ConsensusLayerTestnetConfig(
            config["consensus-layer"]
        )
        self.deposit_contract_address: str = config[
            "deposit-contract-address"
        ]  # hash as str.


class ExecutionLayerTestnetConfig(Config):
    def __init__(self, config: dict):
        super().__init__("execution-testnet-config")

        required_fields = [
            "seconds-per-eth1-block",
            "chain-id",
            "network-id",
            "account-mnemonic",
            "keystore-passphrase",
            "premines",
        ]

        for k in required_fields:
            if k not in config:
                raise Exception(
                    f"Missing required field {k} for ExecutionLayerTestnetConfig: {self.name}"
                )

        self.seconds_per_eth1_block: int = config["seconds-per-eth1-block"]
        self.chain_id: int = config["chain-id"]
        self.network_id: int = config["network-id"]
        self.account_mnemonic: str = config["account-mnemonic"]
        self.keystore_passphrase: str = config["keystore-passphrase"]
        self.premines: dict[str, int] = {}
        for acct, balance in config["premines"].items():
            self.premines[acct] = balance


class ConsensusLayerTestnetConfig(Config):
    """Represents the consensus layer testnet config found in ETBConfig ->
    testnet-config -> consensus-layer."""

    def __init__(self, config: dict):
        super().__init__("consensus-testnet-config")

        required_fields = [
            "preset-base",
            "config-name",
            "min-genesis-active-validator-count",
            "validator-mnemonic",
            # these are required but handled separately.
            "phase0-fork-epoch",
            "phase0-fork-version",
            "altair-fork-epoch",
            "altair-fork-version",
            "bellatrix-fork-epoch",
            "bellatrix-fork-version",
        ]

        for k in required_fields:
            if k not in config:
                raise Exception(
                    f"Missing required field {k} for ConsensusLayerTestnetConfig: {self.name}"
                )

        self.preset_base: PresetEnum
        if config["preset-base"] == "minimal":
            self.preset_base = MinimalPreset
        elif config["preset-base"] == "mainnet":
            self.preset_base = MainnetPreset
        else:
            raise Exception(f"Unknown preset-base {config['preset-base']}")

        self.config_name: str = config["config-name"]
        self.min_genesis_active_validator_count: int = config[
            "min-genesis-active-validator-count"
        ]
        self.validator_mnemonic: str = config["validator-mnemonic"]

        # optional fields that may be overridden in the etb-config file.
        self.min_validator_withdrawability_delay: int = (
            self.preset_base.MIN_VALIDATOR_WITHDRAWABILITY_DELAY.value
        )
        self.shard_committee_period: int = self.preset_base.SHARD_COMMITTEE_PERIOD.value
        self.min_epochs_for_block_requests: int = (
            self.preset_base.MIN_EPOCHS_FOR_BLOCK_REQUESTS.value
        )

        self.phase0_fork: ConsensusFork
        self.altair_fork: ConsensusFork
        self.bellatrix_fork: ConsensusFork
        self.capella_fork: ConsensusFork
        self.deneb_fork: ConsensusFork
        self.sharding_fork: ConsensusFork

        if "min-validator-withdrawability-delay" in config:
            self.min_validator_withdrawability_delay: int = config[
                "min-validator-withdrawability-delay"
            ]

        if "shard-committee-period" in config:
            self.shard_committee_period: int = config["shard-committee-period"]

        if "min-epochs-for-block-requests" in config:
            self.min_epochs_for_block_requests: int = config[
                "min-epochs-for-block-requests"
            ]

        (
            self.phase0_fork,
            self.altair_fork,
            self.bellatrix_fork,
            self.capella_fork,
            self.deneb_fork,
            self.sharding_fork,
        ) = self._get_forks_from_config(config)

        # implicit values
        self.terminal_block_hash: str = TerminalBlockHash
        self.terminal_block_hash_activation_epoch: int = Epoch.FarFuture.value

    def _get_forks_from_config(self, config: dict) -> tuple:
        """Processes the forks in the config and returns a tuple of all
        ConsensusForks for the testnet."""
        required_forks = [
            "phase0",
            "altair",
            "bellatrix",
            "capella",
        ]

        optional_forks = [
            "deneb",
            "sharding",
        ]

        for fork in required_forks:
            if (
                    f"{fork}-fork-epoch" not in config
                    and f"{fork}-fork-version" not in config
            ):
                raise Exception(
                    f"Missing required fork fields for {fork} in ConsensusLayerTestnetConfig: {self.name}"
                )

        fork_version_map = {
            "phase0": ForkVersionName.phase0,
            "altair": ForkVersionName.altair,
            "bellatrix": ForkVersionName.bellatrix,
            "capella": ForkVersionName.capella,
            "deneb": ForkVersionName.deneb,
            "sharding": ForkVersionName.sharding,
        }

        forks = []
        for fork in required_forks:
            forks.append(
                ConsensusFork(
                    fork_name=fork_version_map[fork],
                    fork_version=config[f"{fork}-fork-version"],
                    fork_epoch=config[f"{fork}-fork-epoch"],
                )
            )

        for fork in optional_forks:
            if f"{fork}-fork-version" in config:
                version = config[f"{fork}-fork-version"]
            else:
                version = forks[-1].version + 1

            if f"{fork}-fork-epoch" in config:
                epoch = config[f"{fork}-fork-epoch"]
            else:
                epoch = Epoch.FarFuture.value

            forks.append(
                ConsensusFork(
                    fork_name=fork_version_map[fork],
                    fork_version=version,
                    fork_epoch=epoch,
                )
            )

        return tuple(forks)

    def get_genesis_fork(self) -> ConsensusFork:
        """Returns the current CL fork for genesis.

        @return:
        """
        if self.sharding_fork.epoch == 0:
            return self.sharding_fork
        if self.deneb_fork.epoch == 0:
            return self.deneb_fork
        if self.capella_fork.epoch == 0:
            return self.capella_fork
        if self.bellatrix_fork.epoch == 0:
            return self.bellatrix_fork
        if self.altair_fork.epoch == 0:
            return self.altair_fork
        if self.phase0_fork.epoch == 0:
            return self.phase0_fork
        raise Exception("No genesis fork found")  # should never occur


class ExecutionInstanceConfig(Config):
    """Represents the execution configs for an execution instance.

    These are found in the ETBConfig -> execution-configs
    """

    def __init__(self, name: str, config: dict):
        super().__init__(name)

        self.client: str = config["client"]
        self.launcher: pathlib.Path = config["launcher"]
        self.log_level: str = config["log-level"]
        self.p2p_port: int = config["p2p-port"]
        self.http_apis: List[str] = [x.strip() for x in config["http-apis"].split(",")]
        self.http_port: int = config["http-port"]
        self.ws_apis: List[str] = [x.strip() for x in config["ws-apis"].split(",")]
        self.ws_port: int = config["ws-port"]
        self.engine_http_port: int = config["engine-http-port"]
        self.engine_ws_port: int = config["engine-ws-port"]
        self.metric_port: int = config["metric-port"]
        self.json_rpc_snooper: bool = False
        if "json-snooper-proxy-port" in config:
            self.json_rpc_snooper = True
            self.json_rpc_snooper_proxy_port: int = config["json-snooper-proxy-port"]

    def get_env_vars(self) -> dict[str, str]:
        """Returns the environment variables used by the execution client that
        can be derived from the config.

        This includes all the fields in the config. We prefix with
        EXECUTION to avoid collisions with other env vars. @return:
        env_vars as dict.
        """
        env_vars = {
            "EXECUTION_CLIENT": self.client,
            "EXECUTION_LAUNCHER": str(self.launcher),
            "EXECUTION_LOG_LEVEL": self.log_level,
            "EXECUTION_P2P_PORT": self.p2p_port,
            "EXECUTION_HTTP_APIS": ",".join(self.http_apis),
            "EXECUTION_HTTP_PORT": self.http_port,
            "EXECUTION_WS_APIS": ",".join(self.ws_apis),
            "EXECUTION_WS_PORT": self.ws_port,
            "EXECUTION_ENGINE_HTTP_PORT": self.engine_http_port,
            "EXECUTION_ENGINE_WS_PORT": self.engine_ws_port,
            "EXECUTION_METRIC_PORT": self.metric_port,
            "RUN_JSON_RPC_SNOOPER": self.json_rpc_snooper
        }
        if self.json_rpc_snooper:
            env_vars["CL_EXECUTION_ENGINE_HTTP_PORT"] = self.json_rpc_snooper_proxy_port
        else:
            env_vars["CL_EXECUTION_ENGINE_HTTP_PORT"] = self.engine_http_port

        return env_vars


class ConsensusInstanceConfig(Config):
    """Represents the execution configs for a consensus instance.

    These are found in the ETBConfig -> consensus-configs
    """

    def __init__(self, name: str, config: dict):
        super().__init__(name)

        self.fields = [
            "launcher",
            "log-level",
            "p2p-port",
            "beacon-api-port",
            "beacon-rpc-port",
            "beacon-metric-port",
            "validator-rpc-port",
            "validator-metric-port",
            "num-validators",
        ]

        self.client: str = config["client"]
        self.launcher: pathlib.Path = pathlib.Path(config["launcher"])
        self.log_level: str = config["log-level"]
        self.p2p_port: int = config["p2p-port"]
        self.beacon_api_port: int = config["beacon-api-port"]
        self.beacon_rpc_port: int = config["beacon-rpc-port"]
        self.beacon_metric_port: int = config["beacon-metric-port"]
        # self.validator_api_port: int = config["validator-api-port"]
        self.validator_rpc_port: int = config["validator-rpc-port"]
        self.validator_metric_port: int = config["validator-metric-port"]
        self.num_validators: int = config["num-validators"]

    def get_env_vars(self) -> dict[str, str]:
        """Returns the environment variables used by the consensus client that
        can be derived from the config.

        This includes all the fields in the config. We prefix with
        CONSENSUS to avoid collisions with other env vars. @return:
        env_vars as dict.
        """
        return {
            "CONSENSUS_CLIENT": self.client,
            "CONSENSUS_LAUNCHER": str(self.launcher),
            "CONSENSUS_LOG_LEVEL": self.log_level,
            "CONSENSUS_P2P_PORT": self.p2p_port,
            "CONSENSUS_BEACON_API_PORT": self.beacon_api_port,
            "CONSENSUS_BEACON_RPC_PORT": self.beacon_rpc_port,
            "CONSENSUS_BEACON_METRIC_PORT": self.beacon_metric_port,
            # "CONSENSUS_VALIDATOR_API_PORT": self.validator_api_port,
            "CONSENSUS_VALIDATOR_RPC_PORT": self.validator_rpc_port,
            "CONSENSUS_VALIDATOR_METRIC_PORT": self.validator_metric_port,
        }


class InstanceCollectionConfig(Config):
    """Represents a config for a single instance. This includes everything that
    is required to the minimum fields for a docker-compose entry.
    """

    def __init__(self, name: str, config: dict):
        super().__init__(name)

        required_fields = [
            "image",
            "tag",
            "start-ip-address",
            "num-nodes",
        ]

        for k in required_fields:
            if k not in config:
                raise Exception(
                    f"Missing required field {k} for InstanceCollectionConfig: {name}"
                )

        self.additional_env: dict[str, str] = {}

        self.image: str = config["image"]
        self.tag: str = config["tag"]
        self.start_ip_address: str = config["start-ip-address"]
        self.num_nodes: int = config["num-nodes"]
        self.entrypoint: Union[pathlib.Path, None] = None

        if "entrypoint" in config:
            self.entrypoint: pathlib.Path = pathlib.Path(config["entrypoint"])

        # special case for additional env
        if "additional-env" in config:
            for key, value in config["additional-env"].items():
                if key in self.additional_env:
                    raise Exception(f"Duplicate key {key} in additional-env for {name}")
                self.additional_env[key] = value

    def get_env_vars(self) -> dict[str, str]:
        """Returns the environment variables used by the instance that can be
        derived from the config.

        This includes all additional-env fields in the etb-config
        @return: env_vars as dict.
        """
        env_dict: dict[str, str] = {}
        # some contain additional env vars.
        for key, value in self.additional_env.items():
            env_dict[key.replace("-", "_").upper()] = value

        return env_dict


class ClientInstanceCollectionConfig(InstanceCollectionConfig):
    """Represents a config for a collection of client instances. These are the
    entries found in ETBConfig -> client-instances.
    """

    def __init__(
            self,
            name: str,
            config: dict,
            consensus_config: ConsensusInstanceConfig,
            execution_config: ExecutionInstanceConfig,
    ):
        InstanceCollectionConfig.__init__(self, name, config)

        fields = ["validator-offset-start"]

        for k in fields:
            if k not in config:
                raise Exception(
                    f"Missing required field {k} for ClientInstanceCollectionConfig: {name}"
                )

        self.validator_offset_start: int = config["validator-offset-start"]

        self.consensus_config: ConsensusInstanceConfig = consensus_config
        self.execution_config: ExecutionInstanceConfig = execution_config

        self.collection_dir: pathlib.Path = FilesConfig().local_testnet_dir / self.name

    def get_env_vars(self) -> dict[str, str]:
        """Returns the environment variables used by client instances that can
        be derived from the config.

        This includes all the additional env vars from the config and
        the     fields in the consensus-config and execution-config.
        @return: env_vars as dict.
        """
        env_dict: dict[str, str] = InstanceCollectionConfig.get_env_vars(self)
        env_dict.update(self.consensus_config.get_env_vars())
        env_dict.update(self.execution_config.get_env_vars())
        return env_dict


class Instance:
    """Represents a generic instance. These are the entries found in ETBConfig
    -> generic-instances.

    This object is used to represent one instance from the generic
    instance collections specified in ETBConfig -> generic-instances
    """

    def __init__(
            self,
            collection_name: str,
            ndx: int,
            collection_config: InstanceCollectionConfig,
    ):
        self.collection_name: str = collection_name
        self.ndx: int = ndx
        self.name = f"{collection_name}-{ndx}"
        self.collection_config: InstanceCollectionConfig = collection_config

        self.ip_address: str = self.get_ip_address()

    def __repr__(self):
        return f"{self.name} ({self.ip_address})"

    def __eq__(self, other):
        """Instances will all have unique names.

        @param other: Instance to compare @return: True if the names are
        equal
        """
        return self.name == other.name

    def __neq__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.name)

    def get_ip_address(self) -> str:
        prefix = ".".join(self.collection_config.start_ip_address.split(".")[:3]) + "."
        base = int(self.collection_config.start_ip_address.split(".")[-1])
        return prefix + str(base + int(self.ndx))

    def get_env_vars(self) -> dict:
        """Returns a dict of all non-global env vars that should be set for
        this instance.

        @return:
        """
        # all instances get the following env vars
        env_dict = {
            "IP_ADDRESS": self.ip_address,
        }
        # some contain additional env vars.
        env_dict.update(self.collection_config.get_env_vars())
        return env_dict

    def get_docker_compose_repr(
            self, docker_config: DockerConfig, global_env_vars: dict
    ) -> dict:
        """Returns a dict that represents this instance in a docker-compose
        file.

        @param docker_config: docker config for the experiment (see
        ETBConfig -> docker) @param global_env_vars: global env vars
        that should be set for all instances (passed by ETBConfig)
        @return: the full dict that represents this instance in a
        docker-compose file.
        """

        entry = {
            "container_name": self.name,
            "hostname": self.name,
            "image": f"{self.collection_config.image}:{self.collection_config.tag}",
            "volumes": docker_config.volumes,
            "networks": {docker_config.network_name: {"ipv4_address": self.ip_address}},
        }
        if self.collection_config.entrypoint is not None:
            entry["entrypoint"] = str(self.collection_config.entrypoint).split()
        else:
            entry["entrypoint"] = ["/bin/sh", "-c"]

        if hasattr(self, "docker-command"):
            entry["command"] = self["docker-command"]

        # don't modify the global env vars
        env_vars = global_env_vars.copy()

        for key, value in self.get_env_vars().items():
            env_vars[key] = value

        entry["environment"] = env_vars

        return entry


class ClientInstance(Instance):
    """Represents a client instance. These are the entries found in ETBConfig
    -> client-instances.

    This object is used to represent one instance from the client instance collections specified
    in ETBConfig -> client-instances
    """

    def __init__(
            self,
            root_name: str,
            ndx: int,
            collection_config: ClientInstanceCollectionConfig,
    ):
        Instance.__init__(self, root_name, ndx, collection_config)
        # useful for typing.
        self.collection_config: ClientInstanceCollectionConfig = collection_config
        self.consensus_config: ConsensusInstanceConfig = (
            self.collection_config.consensus_config
        )
        self.execution_config: ExecutionInstanceConfig = (
            self.collection_config.execution_config
        )

        # when clients are started in docker_compose we do a docker-command to
        # start both EL and CL.
        self.docker_command = [
            f"{self.execution_config.launcher} & {self.consensus_config.launcher}"
        ]

        # the etb-client will also pass in some additional attrs for this
        # object to use.
        self.collection_dir: pathlib.Path = (
                FilesConfig().local_testnet_dir / self.collection_name
        )
        self.node_dir: pathlib.Path = (
                FilesConfig().local_testnet_dir / self.collection_name / f"node_{ndx}"
        )
        self.el_dir: pathlib.Path = self.node_dir / self.execution_config.client
        self.jwt_secret_file: pathlib.Path = self.node_dir / "jwt_secret"

        # prysm specific
        self.wallet_password_path: Union[None, pathlib.Path] = None
        self.validator_password: Union[None, str] = None

        if self.consensus_config.client == "prysm":
            self.wallet_password_path = self.node_dir / "wallet-password.txt"
            if "validator-password" not in self.collection_config.additional_env:
                raise Exception(
                    f"prysm config {self.collection_name} validator-password not set in additional-env."
                )
            self.validator_password = self.collection_config.additional_env[
                "validator-password"
            ]

    def get_docker_compose_repr(
            self, docker_config: DockerConfig, global_env_vars: dict
    ) -> dict:
        """Returns a dict that represents this instance in a docker-compose
        file. The client instance docker-repr is a bit different from the
        generic instance docker-repr.

        as it has a bunch of information relevant to the EL and CL
        launcher arguments. @param docker_config: @param
        global_env_vars: @return:
        """
        entry = super().get_docker_compose_repr(docker_config, global_env_vars)
        # client instances need some additional env vars.
        client_specific_env_vars = {
            "JWT_SECRET_FILE": str(self.jwt_secret_file),
            "CONSENSUS_NODE_DIR": str(self.node_dir),
            "COLLECTION_DIR": str(self.collection_dir),
            "CONSENSUS_CONFIG_FILE": str(self.collection_dir / "config.yaml"),
            "CONSENSUS_GENESIS_FILE": str(self.collection_dir / "genesis.ssz"),
            "EXECUTION_NODE_DIR": str(self.el_dir),
            "CONSENSUS_GRAFFITI": f"{self.name}",
        }

        # client instances launch both EL and CL in the same container.
        entry["command"] = self.docker_command
        # add the client specific env vars to the global env vars.
        entry["environment"].update(client_specific_env_vars)
        # add num validators for this entry.
        entry["environment"].update(
            {"NUM_VALIDATORS": self.collection_config.consensus_config.num_validators}
        )

        return entry

    def get_execution_jsonrpc_path(self, protocol: str = "http") -> str:
        """Returns the http path for the jsonrpc interface for this instance.

        Defaults to http @return:
        <protocol>://<ip_address>:<rpc_port>
        """
        if protocol == "http":
            return f"http://{self.ip_address}:{self.execution_config.http_port}"
        if protocol == "ws":
            return f"ws://{self.ip_address}:{self.execution_config.ws_port}"
        raise Exception(f"Invalid protocol: {protocol}")

    def get_consensus_beacon_api_path(self) -> str:
        """Returns the http path for the beacon api for this instance."""
        return f"http://{self.ip_address}:{self.consensus_config.beacon_api_port}"


def _find_used_ip_addresses(config) -> dict[int, str]:
    """
    Scan through the config and find the reserved ips
    @param config:
    @return: all ip suffix's in use.
    """
    ip_addresses = {}
    if "generic-instances" in config:
        for instance_name, instance_config in config["generic-instances"].items():
            if "num-nodes" in instance_config:
                num_nodes = instance_config["num-nodes"]
            else:
                num_nodes = DEFAULT_GENERIC_INSTANCE_NUM_NODES
            if "start-ip-address" in instance_config:
                start_suffix = instance_config["start-ip-address"].split('.')[-1]
                curr_ip: int = int(start_suffix)
                ndx = 0
                for _ in range(num_nodes):
                    if curr_ip in ip_addresses:
                        raise Exception(f"Overlapping ip-range {instance_name} {ip_addresses[curr_ip]}")
                    ip_addresses[curr_ip] = instance_name + str(ndx)
                    ndx += 1
                    curr_ip += 1

    for instance_name, instance_config in config["client-instances"].items():
        if "num-nodes" in instance_config:
            num_nodes = instance_config["num-nodes"]
        else:
            num_nodes = DEFAULT_GENERIC_INSTANCE_NUM_NODES
        if "start-ip-address" in instance_config:
            start_suffix = instance_config["start-ip-address"].split('.')[-1]
            curr_ip = int(start_suffix)
            ndx = 0
            for _ in range(num_nodes):
                if curr_ip in ip_addresses:
                    raise Exception(f"Overlapping ip-range {instance_name} {ip_addresses[curr_ip]}")
                ip_addresses[curr_ip] = instance_name + str(ndx)
                ndx += 1
                curr_ip += 1

    return ip_addresses


class ETBConfig(Config):
    """Represents the ETBConfig file. This is the main config file for the
    testnet.

    This object can be used to get various information about a running
    testnet.
    """

    def __init__(self, path: pathlib.Path):
        """
        @param path: path to the etb-config file.
        """
        super().__init__("etb-config")
        if path.exists():
            with open(path, "r", encoding="utf-8") as etb_config_file:
                self.yaml_config = yaml.safe_load(etb_config_file)
        else:
            raise FileNotFoundError(f"Could not find etb-config file at {path}")

        # where the config file is located.
        self.config_path: pathlib.Path = path
        self.num_client_nodes: int = 0

        if not self._is_populated_by_defaults():
            logging.info("etb-config will be populated with some default values.")
            self._populate_config_with_defaults()

        self.docker: DockerConfig = DockerConfig(self.yaml_config["docker"])
        self.testnet_config: TestnetConfig = TestnetConfig(
            self.yaml_config["testnet-config"]
        )

        self.execution_configs: dict[str, ExecutionInstanceConfig] = {}
        if "execution-configs" in self.yaml_config and self.yaml_config["execution-configs"]:
            for conf in self.yaml_config["execution-configs"]:
                self.execution_configs[conf] = ExecutionInstanceConfig(
                    name=conf, config=self.yaml_config["execution-configs"][conf]
                )

        self.consensus_configs: dict[str, ConsensusInstanceConfig] = {}
        if "consensus-configs" in self.yaml_config and self.yaml_config["consensus-configs"] is not None:
            for conf in self.yaml_config["consensus-configs"]:
                self.consensus_configs[conf] = ConsensusInstanceConfig(
                    name=conf, config=self.yaml_config["consensus-configs"][conf]
                )

        # does this experiment end up forking to deneb
        self.is_deneb = self.testnet_config.consensus_layer.deneb_fork.epoch != Epoch.FarFuture.value

        # optional overrides for the config file.
        if "files" in self.yaml_config:
            self.files: FilesConfig = FilesConfig(self.yaml_config["files"], is_deneb_experiment=self.is_deneb)
        else:
            self.files: FilesConfig = FilesConfig(is_deneb_experiment=self.is_deneb)
        # overwrite so the file written etb-config has all fields written.
        self.yaml_config["files"] = self.files.fields

        # instances should all have the same name, if they don't raise an
        # exception.
        _generic_instance_names: dict[str, None] = {}

        self.generic_instances: dict[str, list[Instance]] = {}
        self.generic_collections: list[InstanceCollectionConfig] = []
        for name in self.yaml_config["generic-instances"]:
            collection_config: InstanceCollectionConfig
            collection_config = InstanceCollectionConfig(
                name=name, config=self.yaml_config["generic-instances"][name]
            )
            self.generic_collections.append(collection_config)
            self.generic_instances[name] = []
            for ndx in range(collection_config.num_nodes):
                instance: Instance = Instance(
                    collection_name=name, ndx=ndx, collection_config=collection_config
                )
                if instance.name in _generic_instance_names:
                    raise Exception(f"Found duplicate instance name: {instance}")
                _generic_instance_names[instance.name] = None
                self.generic_instances[name].append(instance)

        self.client_instances: dict[str, list[ClientInstance]] = {}
        self.client_collections: list[ClientInstanceCollectionConfig] = []
        for name in self.yaml_config["client-instances"]:
            el_config: ExecutionInstanceConfig
            cl_config: ConsensusInstanceConfig
            collection_config: ClientInstanceCollectionConfig

            el_config = self.execution_configs[
                self.yaml_config["client-instances"][name]["execution-config"]
            ]
            cl_config = self.consensus_configs[
                self.yaml_config["client-instances"][name]["consensus-config"]
            ]
            collection_config = ClientInstanceCollectionConfig(
                name=name,
                config=self.yaml_config["client-instances"][name],
                consensus_config=cl_config,
                execution_config=el_config,
            )
            self.client_collections.append(collection_config)

            self.client_instances[name] = []
            for ndx in range(collection_config.num_nodes):
                self.num_client_nodes += 1  # update the client node count.
                instance: ClientInstance = ClientInstance(
                    root_name=name, ndx=ndx, collection_config=collection_config
                )
                if instance.name in _generic_instance_names:
                    raise Exception(f"Found duplicate instance name: {instance}")
                _generic_instance_names[instance.name] = None
                self.client_instances[name].append(instance)

        # dynamic entries set during bootstrap.
        if "dynamic-entries" not in self.yaml_config:
            self.yaml_config["dynamic-entries"] = {}

        self.genesis_time: Union[None, int] = None

        # are we opening ETB config after a testnet has been bootstrapped?
        if "genesis-time" in self.yaml_config["dynamic-entries"]:
            self.genesis_time = int(self.yaml_config["dynamic-entries"]["genesis-time"])

    def _populate_config_with_defaults(self):
        """
        Populate the etb-config to be used in the experiment adding default
        values where fields are not specified.
        @return:
        """
        # get the preset-base
        if "preset-base" not in self.yaml_config["testnet-config"]["consensus-layer"]:
            raise Exception("A preset-base must be supplied in testnet-config/consensus-layer")
        if self.yaml_config["testnet-config"]["consensus-layer"]["preset-base"] == "minimal":
            preset_base = "minimal"
        else:
            preset_base = "mainnet"

        # get the reserved ips and validator ndxs
        self.reserved_ips = _find_used_ip_addresses(self.yaml_config)
        self.curr_ip = 2  # (DEFAULT_IP_PREFIX).2
        # first handle the configs whose default values don't depend on others.
        self._populate_docker_config()
        self.ip_prefix = ".".join(self.yaml_config["docker"]["ip-subnet"].split('.')[:-1]) + '.'
        self._populate_files_config()
        self._populate_execution_configs()
        self._populate_consensus_configs()
        self._populate_generic_instances()
        self.reserved_validators: dict[int, str] = self._get_user_defined_validator_indexes()
        if len(self.reserved_validators.keys()) > 0:
            self.curr_validator_ndx = max(self.reserved_validators.keys())
        else:
            self.curr_validator_ndx = 0
        self._populate_client_instances(preset_base=preset_base)
        self._populate_testnet_config(default_validator_genesis=self.curr_validator_ndx)
        if "special" not in self.yaml_config:
            self.yaml_config["special"] = {}
        self.yaml_config["special"]["is-populated"] = 1
        logging.info("Populated etb-config with default values.")
        logging.info(json.dumps(self.reserved_ips, sort_keys=True, indent=4))

    def _populate_docker_config(self):
        if "docker" not in self.yaml_config:
            self.yaml_config["docker"] = DEFAULT_DOCKER_CONFIG
            return

        default_config = DEFAULT_DOCKER_CONFIG
        default_config = deep_update(default_config, self.yaml_config["docker"])
        self.yaml_config["docker"] = default_config

    def _populate_files_config(self):
        if "files" not in self.yaml_config:
            self.yaml_config["files"] = DEFAULT_FILES_CONFIG
            return

        default_config = DEFAULT_FILES_CONFIG
        default_config = deep_update(default_config, self.yaml_config["files"])
        self.yaml_config["files"] = default_config

    def _populate_execution_configs(self):
        execution_configs = DEFAULT_EXECUTION_CONFIG

        if "execution-configs" in self.yaml_config:
            execution_configs = deep_update(execution_configs, self.yaml_config["execution-configs"])

        for config_name, config in execution_configs.items():
            if "client" not in config:
                raise Exception(f"All supplied execution configs must include a client field. ({config_name}")
            client = config["client"]
            for field in DEFAULT_EXECUTION_CONFIG_FIELDS:
                if field not in config:
                    config[field] = get_default_execution_config_value(client, field)

        self.yaml_config["execution-configs"] = execution_configs

    def _populate_consensus_configs(self):
        consensus_configs = DEFAULT_CONSENSUS_CONFIG

        if "consensus-configs" in self.yaml_config:
            consensus_configs = deep_update(consensus_configs, self.yaml_config["consensus-configs"])

        for config_name, config in consensus_configs.items():
            if "client" not in config:
                raise Exception(f"All supplied consensus configs must include the client field. ({config_name})")
            client = config["client"]
            for field in DEFAULT_CONSENSUS_CONFIG_FIELDS:
                if field not in config:
                    config[field] = get_default_consensus_config_value(client, field)

        self.yaml_config["consensus-configs"] = consensus_configs

    def _populate_generic_instances(self):
        generic_instances = DEFAULT_GENERIC_INSTANCES

        if "generic-instances" in self.yaml_config:
            logging.debug(
                f"Adding user-specified generic-instances to etb-config. {self.yaml_config['generic-instances'].keys()}")
            generic_instances = deep_update(generic_instances, self.yaml_config["generic-instances"])

        for instance_name, instance in generic_instances.items():
            # make sure the required fields are present.
            for field in REQUIRED_GENERIC_INSTANCE_FIELDS:
                if field not in instance:
                    raise Exception(f"Custom instance {instance_name} does not have required field: {field}")
            # add the default num-nodes if not present
            if "num-nodes" not in instance:
                instance["num-nodes"] = DEFAULT_GENERIC_INSTANCE_NUM_NODES

        # handle ip-address mapping
        for instance_name, instance in generic_instances.items():
            if "image" not in instance:
                instance["image"] = DEFAULT_GENERIC_INSTANCE_IMAGE
            if "tag" not in instance:
                instance["tag"] = DEFAULT_GENERIC_INSTANCE_TAG
            if "num-nodes" not in instance:
                instance["num-nodes"] = DEFAULT_GENERIC_INSTANCE_NUM_NODES
            if "start-ip-address" not in instance:
                ip_suffix = self._get_next_available_ip_suffix(instance_name)
                instance["start-ip-address"] = self.ip_prefix + str(ip_suffix)
                for _ in range(instance["num-nodes"]):
                    self.reserved_ips[ip_suffix] = instance_name
                    ip_suffix += 1

        self.yaml_config["generic-instances"] = generic_instances

    def _populate_client_instances(self, preset_base: str):
        if preset_base == "minimal":
            default_tag = DEFAULT_MINIMAL_DOCKER_TAG
            default_image = DEFAULT_MINIMAL_DOCKER_IMAGE
        elif preset_base == "mainnet":
            default_tag = DEFAULT_MAINNET_DOCKER_TAG
            default_image = DEFAULT_MAINNET_DOCKER_IMAGE
        else:
            raise Exception(f"Unknown preset-base {preset_base}")

        consensus_configs = {}
        for name, consensus_config in self.yaml_config["consensus-configs"].items():
            consensus_configs[name] = ConsensusInstanceConfig(name=name, config=consensus_config)

        for instance_name, instance in self.yaml_config["client-instances"].items():
            consensus_config = consensus_configs[instance["consensus-config"]]
            if "num-nodes" not in instance:
                instance["num-nodes"] = DEFAULT_GENERIC_INSTANCE_NUM_NODES
                num_nodes = DEFAULT_GENERIC_INSTANCE_NUM_NODES
            else:
                num_nodes = instance["num-nodes"]
            if "image" not in instance:
                instance["image"] = default_image
            if "tag" not in instance:
                instance["tag"] = default_tag
            if "validator-offset-start" not in instance:
                instance["validator-offset-start"] = self.curr_validator_ndx
                self.curr_validator_ndx += num_nodes * consensus_config["num-validators"]
            if "start-ip-address" not in instance:
                ip_suffix = self._get_next_available_ip_suffix(instance_name)
                instance["start-ip-address"] = self.ip_prefix + str(ip_suffix)
                for _ in range(instance["num-nodes"]):
                    self.reserved_ips[ip_suffix] = instance_name
                    ip_suffix += 1
            # add default additional-envs
            cl_additional_env = DEFAULT_CONSENSUS_CLIENT_INSTANCE_ADDITIONAL_ENV[preset_base][consensus_config.client]
            if cl_additional_env:
                if "additional-env" in instance:
                    instance["additional-env"] = deep_update(instance["additional-env"], cl_additional_env)
                else:
                    instance["additional-env"] = cl_additional_env

    def _populate_testnet_config(self, default_validator_genesis: int):
        testnet_config = DEFAULT_TESTNET_CONFIG

        testnet_config = deep_update(testnet_config, self.yaml_config["testnet-config"])

        if "min-genesis-active-validator-count" not in testnet_config["consensus-layer"]:
            testnet_config["consensus-layer"]["min-genesis-active-validator-count"] = default_validator_genesis

        self.yaml_config["testnet-config"] = testnet_config

    def _get_next_available_ip_suffix(self, client_name) -> int:
        curr_ip = self.curr_ip
        while curr_ip in self.reserved_ips:
            print(f"{curr_ip}, {self.reserved_ips.keys()}")
            curr_ip += 1
        self.curr_ip = curr_ip + 1
        self.reserved_ips[curr_ip] = client_name
        return curr_ip

    def _get_user_defined_validator_indexes(self, config=None) -> dict[int, str]:
        used_validators: dict[int, str] = {}
        if config is None:
            config = self.yaml_config
        # get consensus configs
        consensus_configs = {}
        for name, consensus_config in config["consensus-configs"].items():
            consensus_configs[name] = ConsensusInstanceConfig(name=name, config=consensus_config)
        for instance_name, instance in config["client-instances"].items():
            # we only do this for user-defined validators
            if "validator-offset-start" in instance:
                curr_offset = instance["validator-offset-start"]
                num_validators = consensus_configs[instance["consensus-config"]]["num-validators"]
                num_nodes = instance["num-nodes"]
                for _ in range(num_nodes):
                    for _ in range(num_validators):
                        used_validators[curr_offset] = instance_name
                        curr_offset += 1

        return used_validators

    def _is_populated_by_defaults(self) -> bool:
        if "special" in self.yaml_config and "is-populated" in self.yaml_config["special"]:
            return self.yaml_config["special"]["is-populated"] == 1

    def get_generic_instances(self) -> List[Instance]:
        """Returns a list of all generic instances.
        @return: a list of all generic instances.
        """
        generic_instances: list[Instance] = []
        for instance in self.generic_instances.values():
            generic_instances.extend(instance)
        return generic_instances

    def get_client_instances(self) -> List[ClientInstance]:
        """
        Returns a list of all client instances.
        @return: a list of all client instances.
        """
        client_instances: list[ClientInstance] = []
        for instance in self.client_instances.values():
            client_instances.extend(instance)
        return client_instances

    def get_docker_compose_repr(self) -> dict:
        """Returns a dictionary representation of the docker-compose.yml file.

        @return:
        """
        global_env_vars: dict[str] = {
            "ETB_CONFIG_CHECKPOINT_FILE": str(self.files.etb_config_checkpoint_file),
            "CONSENSUS_CHECKPOINT_FILE": str(self.files.consensus_checkpoint_file),
            "EXECUTION_CHECKPOINT_FILE": str(self.files.execution_checkpoint_file),
            "CONSENSUS_BOOTNODE_CHECKPOINT_FILE": str(
                self.files.consensus_bootnode_checkpoint_file
            ),
            "CONSENSUS_BOOTNODE_FILE": str(self.files.consensus_bootnode_file),
            "IP_SUBNET": str(self.docker.ip_subnet),
            "NUM_CLIENT_NODES": self.num_client_nodes,
            "CHAIN_ID": self.testnet_config.execution_layer.chain_id,
            "NETWORK_ID": self.testnet_config.execution_layer.network_id,
            "IS_DENEB": str(int(self.is_deneb)),  # no boolean in bash
        }

        if self.is_deneb:
            global_env_vars["TRUSTED_SETUP_JSON_FILE"] = str(
                self.files.trusted_setup_json_file
            )
            global_env_vars["TRUSTED_SETUP_TXT_FILE"] = str(
                self.files.trusted_setup_txt_file
            )

        # we also include any overrides from the files config.
        override_files: dict[str, str] = {
            key: self.files.fields[key]
            for key in set(self.files.fields) - set(FilesConfig().fields)
        }
        for key, value in override_files.items():
            global_env_vars[key.upper().replace("-", "_")] = str(value)

        execution_genesis_map: dict[str, str] = {
            "geth": str(self.files.geth_genesis_file),
            "reth": str(self.files.geth_genesis_file),
            "besu": str(self.files.besu_genesis_file),
            "nethermind": str(self.files.nether_mind_genesis_file),
        }

        services: dict = {}
        for instance in self.get_generic_instances():
            services[instance.name] = instance.get_docker_compose_repr(
                docker_config=self.docker, global_env_vars=global_env_vars
            )

        for instance in self.get_client_instances():
            ci_docker_repr = instance.get_docker_compose_repr(
                docker_config=self.docker, global_env_vars=global_env_vars
            )
            # now add the runtime specific env vars.
            if instance.execution_config.client not in execution_genesis_map:
                raise Exception(
                    f"Unknown execution client: {instance.execution_config.client}"
                )
            ci_docker_repr["environment"][
                "EXECUTION_GENESIS_FILE"
            ] = execution_genesis_map[instance.execution_config.client]
            services[instance.name] = ci_docker_repr

        return {
            "services": services,
            "networks": {
                self.docker.network_name: {
                    "driver": "bridge",
                    "ipam": {"config": [{"subnet": self.docker.ip_subnet}]},
                }
            },
        }

    # useful operations.
    def epoch_to_slot(self, epoch: int) -> int:
        """Converts an epoch to a slot.

        @param epoch: @return: slot
        """
        return (
                epoch
                * self.testnet_config.consensus_layer.preset_base.SLOTS_PER_EPOCH.value
        )

    def epoch_to_time(self, epoch: int) -> int:
        """Converts an epoch to a time using the testnet genesis time.

        @param epoch: @return:
        """
        return self.slot_to_time(self.epoch_to_slot(epoch))

    def slot_to_epoch(self, slot: int) -> int:
        """Converts a slot to an epoch.

        @param slot: @return: epoch
        """
        return (
                slot
                // self.testnet_config.consensus_layer.preset_base.SLOTS_PER_EPOCH.value
        )

    def slot_to_time(self, slot: int) -> int:
        """Converts a slot to a time using the testnet genesis time.

        @param slot: time delta in slot form. @return: time as int.
        """
        return self.genesis_time + (
                slot
                * self.testnet_config.consensus_layer.preset_base.SECONDS_PER_SLOT.value
        )

    def get_consensus_fork_delay_seconds(self, fork_name: str) -> int:
        """Returns the number of seconds between genesis and consensus fork.

        @param fork_name: The fork to get the delay for. @return
        : int: how many seconds past genesis the fork should occur.
        """
        epoch_map: dict[str, int] = {
            "phase0": self.testnet_config.consensus_layer.phase0_fork.epoch,
            "altair": self.testnet_config.consensus_layer.altair_fork.epoch,
            "bellatrix": self.testnet_config.consensus_layer.bellatrix_fork.epoch,
            "capella": self.testnet_config.consensus_layer.capella_fork.epoch,
            "deneb": self.testnet_config.consensus_layer.deneb_fork.epoch,
            "sharding": self.testnet_config.consensus_layer.sharding_fork.epoch,
        }
        if fork_name not in epoch_map:
            raise Exception(f"Unknown fork name: {fork_name}")

        fork_epoch: int = epoch_map[fork_name]
        return (
                fork_epoch
                * self.testnet_config.consensus_layer.preset_base.SECONDS_PER_SLOT.value
                * self.testnet_config.consensus_layer.preset_base.SLOTS_PER_EPOCH.value
        )

    # modify the dynamic entries. You shouldn't need to use these.
    def set_genesis_time(self, genesis_time: int):
        """Sets the genesis time for the network in the dynamic_entries.

        @param genesis_time: The time that the bootstrapper started the
        testnet. @return:
        """
        self.yaml_config["dynamic-entries"]["genesis-time"] = genesis_time
        self.genesis_time = genesis_time

    # write an updated version of the config.
    def write_config(self, dest: pathlib.Path):
        """Writes the config to a file.

        This should only be done by the bootstrapper. @return:
        """
        if self.files.etb_config_checkpoint_file.exists():
            raise Exception("Cannot write config file while checkpoint file exists.")

        with open(dest, "w", encoding="utf-8") as etb_config_file:
            yaml.safe_dump(self.yaml_config, etb_config_file, indent=4)


def get_etb_config() -> ETBConfig:
    """Returns the path to the etb-config.yaml file for running containers on
    the network.

    @return
    : network config: ETBConfig
    """
    path = FilesConfig().etb_config_file
    checkpoint = FilesConfig().etb_config_checkpoint_file
    logging.info("Getting ETBConfig for testnet.")
    while not checkpoint.exists():
        time.sleep(1)
        logging.debug(f"Waiting for checkpoint: {checkpoint}")
    return ETBConfig(path)
