from ruamel import yaml
import re

# TODO: use this to clean up client writers.
class ConfigurationEnvironment(object):
    """
    Crawler that goes through all of the configurations of a module
    and grabs the required variables.
    """

    def __init__(self, client_writer):
        self.cw = client_writer
        self.gc = self.cw.gc
        self.cc = self.cw.cc
        self.ecc = None
        self.ccc = None
        if "consensus-config" in self.cc:
            self.ccc = self.gc["consensus-configs"][self.cc["consensus-config"]]
        if "execution-config" in self.cc:
            self.ecc = self.gc["execution-configs"][self.cc["execution-config"]]
        elif "execution-config" in self.ccc:  # cl client with el client
            self.ecc = self.gc["execution-configs"][self.ccc["execution-config"]]

        self.variable_getters = {
            # generic
            "start-ip-addr": self.get_ip,
            "netrestrict-range": self.get_ip_subnet,
            # execution
            "execution-data-dir": self.get_execution_data_dir,
            "execution-p2p-port": self.get_static_port,
            "execution-http-port": self.get_static_port,
            "execution-ws-port": self.get_static_port,
            "http-apis": self.get_execution_config,
            "ws-apis": self.get_execution_config,
            "chain-id": self.get_execution_config,
            "network-id": self.get_execution_config,
            "execution-genesis": self.get_execution_genesis,
            "terminaltotaldifficulty": self.get_ttd,
            # consensus
            "preset-base": self.get_consensus_preset,
            "start-fork": self.get_genesis_fork,
            "end-fork": self.get_end_fork,
            "testnet-dir": self.get_client_config,
            "node-dir": self.get_node_dir,
            "start-consensus-p2p-port": self.get_port,
            "start-beacon-api-port": self.get_port,
            "start-beacon-metric-port": self.get_port,
            "start-beacon-rpc-port": self.get_port,
            "start-validator-rpc-port": self.get_port,
            "start-validator-metric-port": self.get_port,
            "graffiti": self.get_graffiti,
            "execution-launcher": self.get_execution_launcher,
            "local-execution-client": self.get_consensus_config,
            "http-web3-ip-addr": self.get_consensus_config,
            "ws-web3-ip-addr": self.get_consensus_config,
            "consensus-target-peers": self.get_target_peers,
        }

        # how to fetch various ports.
        self.port_maps = {}

    def get_environment_var(self, var):
        if var not in self.variable_getters:
            raise Exception(f"Tried to fetch unimplemented var: {var}.")
        else:
            getter = self.variable_getters[var]
            value = getter(var)
            if getter == self.get_static_port:
                p = re.compile(r"(?P<port>([A-Za-z0-9\-]+-port))")
                m = p.search(var)
                if m is None:
                    raise Exception(f"Unexpected port: {var}")
                variable = m.group("port")
            elif getter == self.get_port:
                p = re.compile(r"start-(?P<port>([A-Za-z0-9\-]+-port))")
                m = p.search(var)
                if m is None:
                    raise Exception(f"Unexpected port: {var}")
                variable = m.group("port")
            elif getter == self.get_ip:
                variable = "ip-addr"
            else:
                variable = var

            return f'{variable.upper().replace("-","_")}={value}'

    # Generic
    def get_client_config(self, var):
        return self.cc[var]

    def get_execution_config(self, var):
        return self.ecc[var]

    def get_consensus_config(self, var):
        return self.ccc[var]

    def get_ip(self, _unused="unused"):
        prefix = ".".join(self.cc["start-ip-addr"].split(".")[:3]) + "."
        base = int(self.cc["start-ip-addr"].split(".")[-1])
        ip = prefix + str(base + self.cw.curr_node)
        return ip

    def get_static_port(self, goal_port):
        return self.get_port(goal_port, static=True)

    def get_port(self, goal_port, static=False):
        if goal_port in self.cc:
            if static:
                return int(self.cc[goal_port])
            return str(int(self.cc[goal_port]) + self.cw.curr_node)
        elif self.ccc is not None and goal_port in self.ccc:
            if static:
                return int(self.ccc[goal_port])
            return str(int(self.ccc[goal_port]) + self.cw.curr_node)
        elif self.ecc is not None and goal_port in self.ecc:
            if static:
                return int(self.ecc[goal_port])
            return str(int(self.ecc[goal_port]) + self.cw.curr_node)
        else:
            raise Exception(f"Can't find a reference to {goal_port}")

    # Global Config
    def get_ttd(self, _unused="unused"):
        return self.gc["config-params"]["execution-layer"]["genesis-config"][
            "terminalTotalDifficulty"
        ]

    def get_execution_genesis(self, _unused="unused"):
        # TODO: generic
        return self.gc["files"]["geth-genesis"]

    def get_ip_subnet(self, _unused="unused"):
        return str(self.gc["docker"]["ip-subnet"])

    def get_consensus_preset(self, _unused="unused"):
        # used for setting correct launcher params.
        return str(self.gc["config-params"]["consensus-layer"]["preset-base"])

    def get_genesis_fork(self, _unused="unused"):
        # used for setting correct launcher params.
        return str(
            self.gc["config-params"]["consensus-layer"]["forks"]["genesis-fork-name"]
        )

    def get_end_fork(self, _unused="unused"):
        # used for setting correct launcher params.
        return str(
            self.gc["config-params"]["consensus-layer"]["forks"]["end-fork-name"]
        )

    # Client Config

    # Execution Config
    def get_execution_client_name(self, _unused="unused"):
        return self.ecc["client"]

    def get_execution_data_dir(self, _unused="unused"):
        if self.ccc is not None:
            return f"{self.get_node_dir()}/{self.get_execution_client_name()}"
        return self.cc["data-dir"]

    # Consensus Config
    def get_execution_launcher(self, _unused="unused"):
        print(self.ccc)
        if self.ccc["local-execution-client"]:
            return str(self.ccc["execution-launcher"])
        else:
            return None

    def get_graffiti(self, _unused="unused"):
        if "graffiti" in self.cc:
            return str(self.cc["graffiti"] + str(self.cw.curr_node))
        else:
            return str(self.cc["client-name"] + str(self.cw.curr_node))

    def get_node_dir(self, _unused="unused"):
        return f"{self.cc['testnet-dir']}/node_{self.cw.curr_node}"

    def get_target_peers(self, _unused="unused"):
        # count the number of consensus nodes in the network and subtract 1
        total_nodes = 0
        for cc in self.gc["consensus-clients"]:
            ccc = self.gc["consensus-configs"][
                self.gc["consensus-clients"][cc]["consensus-config"]
            ]
            total_nodes += ccc["num-nodes"]
        return total_nodes - 1


class ClientWriter(object):
    """
    Generic client class to write services to docker-compose
    Just use this template and add your entrypoint in child class.
    """

    def __init__(self, global_config, client_config, name, curr_node, use_root=False):
        self.use_root = use_root
        self.gc = global_config
        self.cc = client_config
        # used when we have multiple of the same client.
        self.curr_node = curr_node
        # constants.
        self.name = name
        self.image = self.cc["image"]
        self.tag = self.cc["tag"]
        self.network_name = self.gc["docker"]["network-name"]
        self.volumes = [str(x) for x in self.gc["docker"]["volumes"]]

        self.env = []

        # get number of consensus nodes
        self.num_consensus_nodes = 0
        for client in self.gc["consensus-clients"]:
            config = self.gc["consensus-clients"][client]
            ccc = self.gc["consensus-configs"][config["consensus-config"]]
            self.num_consensus_nodes += ccc["num-nodes"]

        self.base_consensus_env_vars = [
            "preset-base",
            "start-fork",
            "end-fork",
            "testnet-dir",
            "node-dir",
            "start-ip-addr",
            "start-consensus-p2p-port",
            "start-beacon-api-port",
            "graffiti",
            "netrestrict-range",
            "start-beacon-metric-port",
            "start-beacon-rpc-port",
            "start-validator-rpc-port",
            "start-validator-metric-port",
            "execution-launcher",
            "local-execution-client",
            "consensus-target-peers",
        ]
        self.consensus_with_execution_env_vars = [
            "http-web3-ip-addr",
            "ws-web3-ip-addr",
        ]
        self.base_execution_env_vars = [
            "start-ip-addr",
            "execution-data-dir",
            "execution-p2p-port",
            "execution-http-port",
            "execution-ws-port",
            "netrestrict-range",
            "http-apis",
            "ws-apis",
            "chain-id",
            "network-id",
            "execution-genesis",
            "terminaltotaldifficulty",
        ]

    # inits for child classes.
    def config(self):
        out = {
            "container_name": self.name,
            "image": f"{self.image}:{self.tag}",
            "volumes": self.volumes,
            "networks": self._networking(),
        }
        if self.use_root:
            out["user"] = "root"
        return out

    def get_config(self):
        config = self.config()
        if "debug" in self.cc:
            if self.cc["debug"]:
                config["entrypoint"] = "/bin/bash"
                config["tty"] = True
                config["stdin_open"] = True
            else:
                config["entrypoint"] = self._entrypoint()
        else:
            config["entrypoint"] = self._entrypoint()
        config["environment"] = self._environment()
        return config

    # override this if neccessary
    def _environment(self):
        return []

    def _networking(self):
        # first calculate the ip.
        return {self.network_name: {"ipv4_address": self.get_ip()}}

    def _entrypoint(self):
        raise Exception("override this method")

    def _config_sanity_check(self):
        """
        Sanity check and report exceptions for configs to help with people
        debugging their own configurations.
        """
        required_ccc_vars = [
            "num-nodes",  # how many beacon nodes
            "num-validators",  # how many validators across all nodes
            "start-consensus-p2p-port",  # the p2p port used by the beacon node
            "start-beacon-api-port",  # the port for the beacon rest api
            "start-beacon-rpc-port",  # some clients have seperate rpc ports
            "start-validator-rpc-port",  # the rpc port for the validator
            "start-beacon-metric-port",  # the port for the metric port
            "local-execution-client",  # if we have a local execution client
        ]
        # if there is a local execution client we must specify the following.
        required_ccc_if_lec = [
            "execution-config",  # the config for the execution client
            "execution-launcher",  # the launch script for the entrypoint
            "http-web3-ip-addr",  # local execution client http port
            "ws-web3-ip-addr",  # local execution client web-sockets port
        ]
        required_cc_vars = [
            "client-name",  # the name of the client, implemented are prysm/lightouse/teku/nimbus
            "image",  # the docker image for that client.
            "tag",  # docker image tag
            "container-name",  # name of the container
            "entrypoint",  # the entrypoint, examples in apps/launchers
            "start-ip-addr",  # ip address for client, incremented based on numnber of nodes.
            "depends",  # ethereum-testnet-bootstrapper client.
            "consensus-config",  # the consensus client config (ccc)
            "testnet-dir",  # the testnet dir to use
            "validator-offset-start",  # the offset to use for validator keys (since we use same mnemonic)
        ]
        # TODO: global config stuff and sanity checks on some vars.
        # client-configs
        for req_cc in required_cc_vars:
            if req_cc not in self.cc:
                raise Exception(
                    f"The client must implement {req_cc} see source comments"
                )

        for req_ccc in required_ccc_vars:
            if req_ccc not in self.ccc:
                raise Exception(
                    f"The consensus config must implement {req_ccc} see source comments"
                )
        if self.ccc["local-execution-client"]:
            for req_ccc in required_ccc_if_lec:
                if req_ccc not in self.ccc:
                    raise Exception(
                        f"The consensus config must implement {req_ccc} when using a local execution client."
                    )

    def get_ip(self, _unused="unused"):
        prefix = ".".join(self.cc["start-ip-addr"].split(".")[:3]) + "."
        base = int(self.cc["start-ip-addr"].split(".")[-1])
        ip = prefix + str(base + self.curr_node)
        return ip


class ConsensusClientWriter(ClientWriter):
    def __init__(self, global_config, client_config, curr_node, use_root=False):
        super().__init__(
            global_config,
            client_config,
            f"{client_config['client-name']}-node-{curr_node}",
            curr_node,
            use_root=use_root,
        )
        self.ccc = global_config["consensus-configs"][client_config["consensus-config"]]
        if self.ccc["local-execution-client"]:
            self.ecc = self.ccc["execution-config"]
        else:
            self.ecc = None

    def _environment(self):
        environment = []
        config_env = ConfigurationEnvironment(self)
        for bcev in self.base_consensus_env_vars:
            environment.append(config_env.get_environment_var(bcev))
        if self.ecc is not None:
            for beev in self.base_execution_env_vars:
                environment.append(config_env.get_environment_var(beev))
            for ceev in self.consensus_with_execution_env_vars:
                environment.append(config_env.get_environment_var(ceev))
        if "consensus-additional-env" in self.cc:
            for k, v in self.cc["consensus-additional-env"].items():
                environment.append(f'{k.upper().replace("-","_")}={v}')
        return list(set(environment))


class ExecutionClientWriter(ClientWriter):
    def __init__(self, global_config, client_config, curr_node):
        super().__init__(
            global_config,
            client_config,
            f"{client_config['client-name']}-node-{curr_node}",
            curr_node,
        )
        self.ecc = global_config["execution-configs"][client_config["execution-config"]]

    def _environment(self):
        environment = []
        config_env = ConfigurationEnvironment(self)
        for beev in self.base_execution_env_vars:
            environment.append(config_env.get_environment_var(beev))
        return environment


class GethClientWriter(ExecutionClientWriter):
    def __init__(self, global_config, client_config, curr_node):
        super().__init__(global_config, client_config, curr_node)
        self.out = self.config()

    def _entrypoint(self):
        return [self.cc["entrypoint"]]


class TekuClientWriter(ConsensusClientWriter):
    def __init__(self, global_config, client_config, curr_node):
        super().__init__(
            global_config,
            client_config,
            curr_node,
            use_root=True,
        )
        self.out = self.config()

    def _entrypoint(self):
        return [self.cc["entrypoint"]]


class LighthouseClientWriter(ConsensusClientWriter):
    def __init__(self, global_config, client_config, curr_node):
        super().__init__(
            global_config,
            client_config,
            curr_node,
        )
        self.out = self.config()

    def _entrypoint(self):
        return [self.cc["entrypoint"]]


class NimbusClientWriter(ClientWriter):
    def __init__(self, global_config, client_config, curr_node):
        super().__init__(
            global_config,
            client_config,
            f"nimbus-consensus-client-{curr_node}",
            curr_node,
        )
        self.out = self.config()

    def _entrypoint(self):
        """
        DEBUG_LEVEL=$1
        TESTNET_DIR=$2
        NODE_DIR=$3
        ETH1_ENDPOINT=$4
        IP_ADDR=$5
        P2P_PORT=$6
        RPC_PORT=$7
        METRICS_PORT=$9
        TTD=$10
        """
        return [
            self.get_launcher(),
            self.get_consensus_preset(),
            self.get_genesis_fork(),
            self.get_end_fork(),
            self.cc["debug-level"],
            self.get_testnet_dir(),
            self.get_node_dir(),
            self.get_web3_ws(),
            self.get_ip(),
            self.get_port("p2p"),
            self.get_port("rpc"),
            self.get_port("rest"),
            self.get_port("metric"),
            self.get_ttd(),
            self.get_consensus_target_peers(),
        ]


class PrysmClientWriter(ConsensusClientWriter):
    def __init__(self, global_config, client_config, curr_node):
        super().__init__(
            global_config,
            client_config,
            curr_node,
        )
        self.out = self.config()

    def _entrypoint(self):
        return [self.cc["entrypoint"]]


class Eth2BootnodeClientWriter(ClientWriter):
    def __init__(self, global_config, client_config, curr_node):
        super().__init__(
            global_config, client_config, f"eth2-bootnode-{curr_node}", curr_node
        )
        self.out = self.config()

    def _entrypoint(self):
        """
        ./launch-bootnode <ip-address> <enr-port> <api-port> <private-key> <enr-path>
        launches a bootnode with a web port for fetching the enr, and
        fetches that enr and puts it in the local dir for other clients
        to find..
        """
        return [
            str(self.cc["entrypoint"]),
            str(self.get_ip()),
            str(self.cc["enr-udp"]),
            str(self.cc["api-port"]),
            str(self.cc["private-key"]),
            str(self.cc["bootnode-enr-file"]),
        ]


class GethBootnodeClientWriter(ClientWriter):
    def __init__(self, global_config, client_config, curr_node):
        super().__init__(
            global_config, client_config, f"geth-bootnode-{curr_node}", curr_node
        )
        self.out = self.config()

    def _entrypoint(self):
        """
        ./launch-bootnode <ip-address> <enr-port> <api-port> <private-key> <enr-path>
        launches a bootnode with a web port for fetching the enr, and
        fetches that enr and puts it in the local dir for other clients
        to find..
        """
        return [
            str(self.cc["entrypoint"]),
            str(self.cc["data-dir"]),
            self.get_ip(),
            self.get_port("execution-p2p"),
        ]


class GenericModule(ClientWriter):
    def __init__(self, global_config, client_config, curr_node):
        super().__init__(
            global_config, client_config, client_config["container-name"], curr_node
        )
        self.out = self.config()

    def _entrypoint(self):
        if isinstance(self.cc["entrypoint"], str):
            return self.cc["entrypoint"].split()

        else:
            return self.cc["entrypoint"]


class TestnetBootstrapper(ClientWriter):
    def __init__(self, global_config, client_config):
        super().__init__(
            global_config, client_config, client_config["container-name"], 0
        )
        self.out = self.config()

    def _entrypoint(self):
        return [
            "/source/entrypoint.sh",
            "--config",
            self.cc["config-file"],
            "--no-docker-compose",
        ]


class DockerComposeWriter(object):
    def __init__(self, global_config):
        self.gc = global_config
        self.yaml = self._base()
        self.client_writers = {
            "teku": TekuClientWriter,
            "prysm": PrysmClientWriter,
            "lighthouse": LighthouseClientWriter,
            "nimbus": NimbusClientWriter,
            "geth-bootstrapper": GethClientWriter,
            "ethereum-testnet-bootstrapper": TestnetBootstrapper,
            "generic-module": GenericModule,
            "eth2-bootnode": Eth2BootnodeClientWriter,
            "geth-bootnode": GethBootnodeClientWriter,
        }

    def _base(self):
        return {
            "services": {},
            "networks": {
                self.gc["docker"]["network-name"]: {
                    "driver": "bridge",
                    "ipam": {"config": [{"subnet": self.gc["docker"]["ip-subnet"]}]},
                }
            },
        }

    def add_services(self):
        # keep testnet-bootstrapper seperate
        client_modules = [
            "execution-clients",
            "generic-modules",
            "consensus-bootnodes",
            "execution-bootnodes",
        ]

        for module in client_modules:
            if module in self.gc:
                for client_module in self.gc[module]:
                    config = self.gc[module][client_module]
                    if not "client-name" in config:
                        exception = f"module {module}, {client_module} expects client-name attribute\n"
                        exception += f"\tfound: {config.keys()}\n"
                        raise Exception(exception)
                    client = config["client-name"]
                    for n in range(config["num-nodes"]):
                        if module == "generic-modules":
                            writer = self.client_writers["generic-module"](
                                self.gc, config, n
                            )
                        else:
                            writer = self.client_writers[client](self.gc, config, n)
                        self.yaml["services"][writer.name] = writer.get_config()

        for consensus_client in self.gc["consensus-clients"]:
            config = self.gc["consensus-clients"][consensus_client]
            print(config)
            consensus_config = self.gc["consensus-configs"][config["consensus-config"]]
            client = config["client-name"]
            for n in range(consensus_config["num-nodes"]):
                writer = self.client_writers[client](self.gc, config, n)
                self.yaml["services"][writer.name] = writer.get_config()
        # last we check for bootstrapper, if present all dockers must
        # depend on this.
        if "testnet-bootstrapper" in self.gc:
            for client in self.gc["testnet-bootstrapper"]:
                tbc = self.gc["testnet-bootstrapper"][client]
                tbw = self.client_writers[client](self.gc, tbc)
                for service in self.yaml["services"]:
                    self.yaml["services"][service]["depends_on"] = [tbw.name]
                self.yaml["services"][tbw.name] = tbw.get_config()


def generate_docker_compose(global_config):
    dcw = DockerComposeWriter(global_config)
    dcw.add_services()
    return dcw.yaml
