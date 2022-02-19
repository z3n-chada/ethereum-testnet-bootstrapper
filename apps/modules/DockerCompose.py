from ruamel import yaml


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

        # get number of consensus nodes
        self.num_consensus_nodes = 0
        for client in self.gc["consensus-clients"]:
            config = self.gc["consensus-clients"][client]
            self.num_consensus_nodes += config["num-nodes"]

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
        if "environment" in self.cc:
            config["environment"] = [str(x) for x in self.cc["environment"]]
        return config

    def _networking(self):
        # first calculate the ip.
        return {self.network_name: {"ipv4_address": self.get_ip()}}

    """
        Popular args across all clients
    """

    def get_ip(self):
        prefix = ".".join(self.cc["ip-start"].split(".")[:3]) + "."
        base = int(self.cc["ip-start"].split(".")[-1])
        ip = prefix + str(base + self.curr_node)
        return ip

    def get_testnet_dir(self):
        return str(self.cc["testnet-dir"])

    def get_node_dir(self):
        return f"{self.cc['testnet-dir']}/node_{self.curr_node}"

    def get_ip_subnet(self):
        return str(self.gc["docker"]["ip-subnet"])

    def get_port(self, port_name):
        return str(int(self.cc[f"start-{port_name}-port"]) + self.curr_node)

    def get_launcher(self):
        return str(self.cc["entrypoint"])

    def get_web3_http(self):
        geth_config = self.gc["execution-clients"]["geth-bootstrapper"]
        return f"http://{geth_config['ip-start']}:{geth_config['http-port']}"

    def get_web3_ws(self):
        geth_config = self.gc["execution-clients"]["geth-bootstrapper"]
        return f"ws://{geth_config['ip-start']}:{geth_config['ws-port']}"

    def get_web3_ipc(self):
        geth_config = self.gc["execution-clients"]["geth-bootstrapper"]
        return geth_config["geth-data-dir"] + "/geth.ipc"

    def get_ttd(self):
        return str(
            self.gc["config-params"]["execution-layer"]["genesis-config"][
                "terminalTotalDifficulty"
            ]
        )

    def get_consensus_preset(self):
        # used for setting correct launcher params.
        return str(self.gc["config-params"]["consensus-layer"]["preset-base"])

    def get_genesis_fork(self):
        # used for setting correct launcher params.
        return str(
            self.gc["config-params"]["consensus-layer"]["forks"]["genesis-fork-name"]
        )

    def get_end_fork(self):
        # used for setting correct launcher params.
        return str(
            self.gc["config-params"]["consensus-layer"]["forks"]["end-fork-name"]
        )

    def get_consensus_target_peers(self):
        return str(self.num_consensus_nodes - 1)

    def _entrypoint(self):
        raise Exception("override this method")


class GethClientWriter(ClientWriter):
    def __init__(self, global_config, client_config, curr_node):
        super().__init__(
            global_config, client_config, f"geth-node-{curr_node}", curr_node
        )
        self.out = self.config()

    def _entrypoint(self):
        """
        Usage:
        GETH_DATA_DIR
        GENESIS_CONFIG
        NETWORK_ID
        HTTP_PORT
        HTTP_APIS
        WS_PORT
        WS_APIS
        IP_ADDR
        TESTNET_IP_RANGE
        TTD
        """
        return [
            str(self.cc["entrypoint"]),
            str(self.cc["geth-data-dir"]),
            str(self.gc["files"]["geth-genesis"]),
            str(self.cc["network-id"]),
            str(self.cc["http-port"]),
            str(self.cc["http-apis"]),
            str(self.cc["ws-port"]),
            str(self.cc["ws-apis"]),
            str(self.get_ip()),
            self.get_ip_subnet(),
            self.get_ttd(),
        ]


class TekuClientWriter(ClientWriter):
    def __init__(self, global_config, client_config, curr_node):
        super().__init__(
            global_config,
            client_config,
            f"teku-consensus-client-{curr_node}",
            curr_node,
            use_root=True,
        )
        self.out = self.config()

    def _entrypoint(self):
        """
        DEBUG_LEVEL=$1
        TESTNET_DIR=$2
        NODE_DIR=$3
        P2P_PORT=$4
        METRIC_PORT=$5
        REST_PORT=$6
        ETH1_ENDPOINT=$7
        """

        return [
            self.get_launcher(),
            self.get_consensus_preset(),
            self.get_genesis_fork(),
            self.get_end_fork(),
            self.cc["debug-level"],
            self.get_testnet_dir(),
            self.get_node_dir(),
            self.get_web3_http(),
            self.get_ip(),
            self.get_port("p2p"),
            self.get_port("rest"),
            self.get_port("http"),
        ]

        # return [
        #    str(self.cc["entrypoint"]),
        #    str(self.cc["debug-level"]),
        #    str(self.cc["testnet-dir"]),
        #    f"{testnet_dir}/node_{self.curr_node}",
        #    f'http://{geth_config["ip-start"]}:{geth_config["http-port"]}',
        #    str(self.get_ip()),
        #    str(int(self.cc["start-p2p-port"]) + self.curr_node),
        #    str(int(self.cc["start-rest-port"]) + self.curr_node),
        #    str(int(self.cc["start-http-port"]) + self.curr_node),
        # ]


class LighthouseClientWriter(ClientWriter):
    def __init__(self, global_config, client_config, curr_node):
        super().__init__(
            global_config,
            client_config,
            f"lighthouse-consensus-client-{curr_node}",
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
        REST_PORT=$7
        HTTP_PORT=$8
        METRICS_PORT=$9
        TTD_OVERRIDE=${10}
        """
        return [
            self.get_launcher(),
            self.get_consensus_preset(),
            self.get_genesis_fork(),
            self.get_end_fork(),
            self.cc["debug-level"],
            self.get_testnet_dir(),
            self.get_node_dir(),
            self.get_web3_http(),
            self.get_ip(),
            self.get_port("p2p"),
            self.get_port("rest"),
            self.get_port("http"),
            self.get_port("metric"),
            self.get_ttd(),
            self.get_consensus_target_peers(),
        ]


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


class PrysmClientWriter(ClientWriter):
    def __init__(self, global_config, client_config, curr_node):
        super().__init__(
            global_config,
            client_config,
            f"prysm-consensus-client-{curr_node}",
            curr_node,
        )
        self.out = self.config()

    def _entrypoint(self):
        """
        PRESET_BASE=$1
        STARK_FORK=$2
        END_FORK=$3
        DEBUG_LEVEL=$4
        TESTNET_DIR=$5
        NODE_DATADIR=$6
        WEB3_PROVIDER=$7
        IP_ADDR=$8
        P2P_PORT=$9
        METRICS_PORT=${10}
        RPC_PORT=${11}
        GRPC_PORT=${12}
        VALIDATOR_METRICS_PORT=${13}
        GRAFFITI=${14}
        NETRESTRICT_RANGE=${15}
        """
        return [
            self.get_launcher(),
            self.get_consensus_preset(),
            self.get_genesis_fork(),
            self.get_end_fork(),
            self.cc['debug-level'],
            self.get_testnet_dir(),
            self.get_node_dir(),
            self.get_web3_http(),
            self.get_ip(),
            self.get_port("p2p"),
            self.get_port("metric"),
            self.get_port("rpc"),
            self.get_port("grpc"),
            self.get_port("validator-metrics"),
            str(self.cc["graffiti"] + str(self.curr_node)),
            self.get_ip_subnet(),
        ]


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


class GenericModule(ClientWriter):
    def __init__(self, global_config, client_config, curr_node):
        super().__init__(
            global_config, client_config, client_config["container-name"], curr_node
        )
        self.out = self.config()

    def _entrypoint(self):
        return self.cc["entrypoint"]


class TestnetBootstrapper(ClientWriter):
    def __init__(self, global_config, client_config):
        super().__init__(
            global_config, client_config, client_config["container-name"], 0
        )
        self.out = self.config()

    def _entrypoint(self):
        return [
            "/work/entrypoint.sh",
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
            "consensus-clients",
            "execution-clients",
            "generic-modules",
            "consensus-bootnodes",
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
