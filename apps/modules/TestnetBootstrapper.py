import logging
import os
import random
import shutil
import time
from pathlib import Path

from ruamel import yaml

from .ConsensusBootstrapper import ETBConsensusBootstrapper
from .DockerCompose import generate_docker_compose
from .ETBConfig import ETBConfig
from .ExecutionBootstrapper import ETBExecutionBootstrapper
from .ExecutionRPC import (ETBExecutionRPC, admin_add_peer_RPC,
                           admin_node_info_RPC)

logger = logging.getLogger("bootstrapper_log")


class EthereumTestnetBootstrapper(object):
    """
    Creates docker-compose.yaml file to bootstrap a testnet.
    The docker-compose will call back into this module to perform all
    of the needed tasks.
    """

    def __init__(self, config_path):
        self.etb_config = ETBConfig(config_path)
        self.config_path = config_path

    def create_testnet_directory_structure(self):

        # testnet dir
        Path(self.etb_config.get("testnet-dir")).mkdir()

        # create the execution-client dirs
        logger.info("Creating execution client directories")
        for name, ec in self.etb_config.get("execution-clients").items():
            Path(ec.get("execution-data-dir")).mkdir()

        # create consensus client dirs and their cooresponding execution dirs
        logger.info("Createing consensus client directories")
        for name, cc in self.etb_config.get("consensus-clients").items():
            Path(cc.get("testnet-dir")).mkdir()
            for node in range(cc.get("num-nodes")):
                node_path = Path(cc.get("node-dir", node))
                node_path.mkdir()
                if cc.has_local_exectuion_client:
                    ec_path = node_path.joinpath(
                        cc.get("execution-config").get("client")
                    )
                    ec_path.mkdir()

        for name, cbc in self.etb_config.get("consensus-bootnodes").items():
            bootnode_path = Path(cbc.get("consensus-bootnode-enr-file"))
            bootnode_path.parents[0].mkdir(exist_ok=True)

        shutil.copy(self.config_path, self.etb_config.get("bootstrap-config-file"))

    def init_bootstrapper(self):
        """
        Init all of the files and directories that we will need when we run
        the bootstrapper.
        """
        # before we start generating ssz files we first create all
        # of the dirs and sub-dirs.
        self.clear_last_run()
        self.create_testnet_directory_structure()

        execution_bootstrapper = ETBExecutionBootstrapper(self.etb_config)
        # we use this in order to get calculatable enodes.
        execution_bootstrapper.create_erigon_nodekey_files()
        # go ahead and do jwt.
        for items, cc in self.etb_config.get("consensus-clients").items():
            if cc.has("jwt-secret-file"):
                for node in range(cc.get("num-nodes")):
                    jwt_secret = f"0x{random.randbytes(32).hex()}"
                    jwt_secret_file = cc.get("jwt-secret-file", node)
                    with open(jwt_secret_file, "w") as f:
                        f.write(jwt_secret)

        for name, ec in self.etb_config.get("execution-clients").items():
            if ec.has("jwt-secret-file"):
                for node in range(ec.get("num-nodes")):
                    jwt_secret = f"0x{random.randbytes(32).hex()}"
                    jwt_secret_file = ec.get("jwt-secret-file", node)
                    with open(jwt_secret_file, "w") as f:
                        f.write(jwt_secret)

        logger.info("Finished initing the testnet")

    def bootstrap_testnet(self, enable_resume=False):
        # bail out if we are resuming a testnet.
        if enable_resume:
            if Path(self.etb_config.get("resumable-checkpoint-file")).is_file():
                logger.info("Resuming an already started testnet experiment.")
                self.link_all_execution_clients()
                return
        # when we bootstrap the testnet we must do the following.

        # write now() to the config file so all modules have the same reference time.
        self.etb_config.set_bootstrap_genesis(int(time.time()))

        with open(self.etb_config.get("etb-config-file"), "w") as f:
            yaml.safe_dump(self.etb_config.config, f)

        # consensus bootstrappers have no dependency so just signal them.
        cbncf = self.etb_config.get("consensus-bootnode-checkpoint-file")
        with open(cbncf, "w") as f:
            f.write("1")

        # next the execution clients.
        execution_bootstrapper = ETBExecutionBootstrapper(self.etb_config)
        execution_bootstrapper.bootstrap_execution_clients()
        # we are done here, go ahead and allow execution clients to start.
        e_checkpoint = self.etb_config.get("execution-checkpoint-file")
        with open(e_checkpoint, "w") as f:
            f.write("1")

        consensus_bootstrapper = ETBConsensusBootstrapper(self.etb_config)
        consensus_bootstrapper.bootstrap_consensus_clients()

        # nimbus has issues. so launch all of the el clients, link them (which
        # should force besu to start syncing and serve RPC, then launch nimbus)

        # with open(self.etb_config.get("consensus-checkpoint-file"), "w") as f:
        #     f.write("1")

        # go ahead and get the enode of all non-erigon clients.
        etb_rpc = ETBExecutionRPC(self.etb_config, timeout=5)

        logger.info(
            "TestnetBootstrapper: Gathering enode info for clients that support it."
        )
        admin_rpc_nodes = self.get_all_clients_with_admin_rpc_api()
        node_info = etb_rpc.do_rpc_request(
            admin_node_info_RPC(), client_nodes=admin_rpc_nodes, all_clients=False
        )

        enodes = {}
        for name, info in node_info.items():
            enodes[name] = info["result"]["enode"]

        print(enodes, flush=True)

        erigon_enodes = execution_bootstrapper.get_erigon_enodes()

        all_enodes = list(enodes.values()) + erigon_enodes

        enode_list = ",".join(all_enodes)

        print(enode_list, flush=True)

        with open(self.etb_config.get("execution-enodes-file"), "w") as f:
            f.write(enode_list)
        # create the erigon-static-peers file
        with open(self.etb_config.get("erigon-checkpoint-file"), "w") as f:
            f.write("1")

        with open(self.etb_config.get("consensus-checkpoint-file"), "w") as f:
            f.write("1")

        for enode in all_enodes:
            etb_rpc.do_rpc_request(
                admin_add_peer_RPC(enode),
                client_nodes=admin_rpc_nodes,
                all_clients=False,
            )
            time.sleep(1)

        # now we need to add the erigon enodes.
        # with open(self.etb_config.get("consensus-checkpoint-file"), "w") as f:
        #     f.write("1")

        # logger.info("TestnetBootstrapper: Peering the execution clients")
        # logger.debug(f"enodes: {enodes}")
        # for enode in enodes.values():
        #     etb_rpc.do_rpc_request(admin_add_peer_RPC(enode), all_clients=True)
        #     time.sleep(1)
        with open(self.etb_config.get("consensus-checkpoint-file"), "w") as f:
            f.write("1")

        # now that we have everything running, if enable-resume is detected.
        if enable_resume:
            logger.info(
                "Enable-resume detected... adding the resumable checkpoint file"
            )
            with open(self.etb_config.get("resumable-checkpoint-file"), "w") as f:
                f.write("1")

    def clear_last_run(self):
        testnet_root = self.etb_config.get("testnet-root")
        for file in os.listdir(testnet_root):
            path = Path(os.path.join(testnet_root, file))
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

    def write_docker_compose(self):
        logger.info("Creating docker-compose file")
        docker_path = self.etb_config.get("docker-compose-file")
        docker_compose = generate_docker_compose(self.etb_config)
        with open(docker_path, "w") as f:
            yaml.safe_dump(docker_compose, f)

    def get_all_clients_with_admin_rpc_api(self):
        # use this method to make sure we only used the admin rpc interface with clients
        # that accept it.
        clients = []
        for name, ec in self.etb_config.get("execution-clients").items():
            if "admin" in ec.get("http-apis").lower():
                for n in range(ec.get("num-nodes")):
                    clients.append(f"{name}-{n}")
        # consensus clients with execution clients using admin rpc
        for name, cc in self.etb_config.get("consensus_clients").items():
            if cc.has("local-execution-client") and cc.get("local-execution-client"):
                if "admin" in cc.execution_config.get("http-apis").lower():
                    for n in range(ec.get("num-nodes")):
                        clients.append(f"{name}-{n}")

        return clients

    def link_all_execution_clients(self):

        etb_rpc = ETBExecutionRPC(self.etb_config, timeout=5)

        logger.info(
            "TestnetBootstrapper: Gathering enode info for clients that support it."
        )
        admin_rpc_nodes = self.get_all_clients_with_admin_rpc_api()
        node_info = etb_rpc.do_rpc_request(
            admin_node_info_RPC(), client_nodes=admin_rpc_nodes, all_clients=False
        )

        enodes = {}

        for name, info in node_info.items():
            enodes[name] = info["result"]["enode"]

        print(enodes, flush=True)

        erigon_enodes = execution_bootstrapper.get_erigon_enodes()

        all_enodes = list(enodes.values()) + erigon_enodes

        enode_list = ",".join(all_enodes)

        print(enode_list, flush=True)

        for enode in all_enodes:
            etb_rpc.do_rpc_request(
                admin_add_peer_RPC(enode),
                client_nodes=admin_rpc_nodes,
                all_clients=False,
            )
            time.sleep(1)

