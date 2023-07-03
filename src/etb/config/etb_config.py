import logging
import pathlib
import time
from typing import List, Union

from ruamel import yaml

from ..common.consensus import ConsensusFork, TerminalBlockHash
from ..common.consensus import (
    PresetEnum,
    MinimalPreset,
    MainnetPreset,
    ForkVersionName,
    Epoch,
)


class Config:
    """Represents a config object.

    The only difference between this and a regular object is the easy
    mapping of fields that use hyphens v.s. underscores.
    """

    def __init__(self, name: str):
        self.name: str = name

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

    def __init__(self, optional_overrides=None):
        super().__init__("files")

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

    def get_env_vars(self) -> dict[str, str]:
        """Returns the environment variables used by the execution client that
        can be derived from the config.

        This includes all the fields in the config. We prefix with
        EXECUTION to avoid collisions with other env vars. @return:
        env_vars as dict.
        """
        return {
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
        }


class ConsensusInstanceConfig(Config):
    """Represents the execution configs for a consensus instance.

    These are found in the ETBConfig -> consensus-configs
    """

    def __init__(self, name: str, config: dict):
        super().__init__(name)

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
                self._config = yaml.safe_load(etb_config_file)
        else:
            raise FileNotFoundError(f"Could not find etb-config file at {path}")

        # where the config file is located.
        self.config_path: pathlib.Path = path
        self.num_client_nodes: int = 0

        # optional overrides for the config file.
        if "files" in self._config:
            self.files: FilesConfig = FilesConfig(self._config["files"])
        else:
            self.files: FilesConfig = FilesConfig()
        # overwrite so the file written etb-config has all fields written.
        self._config["files"] = self.files.fields

        self.docker: DockerConfig = DockerConfig(self._config["docker"])
        self.testnet_config: TestnetConfig = TestnetConfig(
            self._config["testnet-config"]
        )

        self.execution_configs: dict[str, ExecutionInstanceConfig] = {}
        for conf in self._config["execution-configs"]:
            self.execution_configs[conf] = ExecutionInstanceConfig(
                name=conf, config=self._config["execution-configs"][conf]
            )

        self.consensus_configs: dict[str, ConsensusInstanceConfig] = {}
        for conf in self._config["consensus-configs"]:
            self.consensus_configs[conf] = ConsensusInstanceConfig(
                name=conf, config=self._config["consensus-configs"][conf]
            )

        # instances should all have the same name, if they don't raise an
        # exception.
        _generic_instance_names: dict[str, None] = {}

        self.generic_instances: dict[str, list[Instance]] = {}
        self.generic_collections: list[InstanceCollectionConfig] = []
        for name in self._config["generic-instances"]:
            collection_config: InstanceCollectionConfig
            collection_config = InstanceCollectionConfig(
                name=name, config=self._config["generic-instances"][name]
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
        for name in self._config["client-instances"]:
            el_config: ExecutionInstanceConfig
            cl_config: ConsensusInstanceConfig
            collection_config: ClientInstanceCollectionConfig

            el_config = self.execution_configs[
                self._config["client-instances"][name]["execution-config"]
            ]
            cl_config = self.consensus_configs[
                self._config["client-instances"][name]["consensus-config"]
            ]
            collection_config = ClientInstanceCollectionConfig(
                name=name,
                config=self._config["client-instances"][name],
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
        if "dynamic-entries" not in self._config:
            self._config["dynamic-entries"] = {}

        self.genesis_time: Union[None, int] = None

        # are we opening ETB config after a testnet has been bootstrapped?
        if "genesis-time" in self._config["dynamic-entries"]:
            self.genesis_time = int(self._config["dynamic-entries"]["genesis-time"])

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
        }

        # we also include any overrides from the files config.
        override_files: dict[str, str] = {
            key: self.files.fields[key]
            for key in set(self.files.fields) - set(FilesConfig().fields)
        }
        for key, value in override_files.items():
            global_env_vars[key.upper().replace("-", "_")] = str(value)

        execution_genesis_map: dict[str, str] = {
            "geth": str(self.files.geth_genesis_file),
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
        self._config["dynamic-entries"]["genesis-time"] = genesis_time
        self.genesis_time = genesis_time

    # write an updated version of the config.
    def write_config(self, dest: pathlib.Path):
        """Writes the config to a file.

        This should only be done by the bootstrapper. @return:
        """
        if self.files.etb_config_checkpoint_file.exists():
            raise Exception("Cannot write config file while checkpoint file exists.")
        with open(dest, "w", encoding="utf-8") as etb_config_file:
            yaml.safe_dump(self._config, etb_config_file)


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
