"""
    This module is the glue to tie together all the execution and consensus client bootstrapping
    phases. There is a high level doc in docs that discusses this process.
"""
import logging
import os
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
    The Testnet Bootstrapper wraps all the consensus and execution
    bootstrapper logic to bootstrap all the clients. It also handles
    the consensus bootnode.

    The EthereumTestnetBootstrapper is used to init the testnet and later is
    used to bootstrap and run the testnet.
    """

    def __init__(self, config_path):
        self.etb_config = ETBConfig(config_path)
        self.config_path = config_path

    def init_testnet(self):
        """
        The init routine simply processes the etb-config file and performs all
        the work that can be done statically. This includes creating the dir
        structure for the testnet and populating the cl bootnode enr file.
        """
        # clear the last run
        self.clear_last_run()

        # testnet dir
        Path(self.etb_config.get("testnet-dir")).mkdir()

        # create the stand-alone execution-client dirs and jwt secrets
        eb = ETBExecutionBootstrapper(self.etb_config)
        eb.create_stand_alone_execution_dirs()
        eb.create_execution_client_jwt()

        # create consensus client dirs and their corresponding execution client dirs.
        cb = ETBConsensusBootstrapper(self.etb_config)
        cb.create_consensus_dirs()
        cb.create_consensus_client_jwt()

        self._write_docker_compose()
        self._write_consensus_bootnode_enr()

        # copy in the config file we used for the init process.
        shutil.copy(self.config_path, self.etb_config.get("etb-config-file"))

    def bootstrap_testnet(self):
        """
        This routine bootstraps the testnet. The general process is as follows:
        1. open the etb_config file and write the current time.
        2. signal the consensus bootnode to come online.
        3. create the execution genesis files and then signal those clients to
           come online.
        """
        # bootstrappers
        el_bootstrapper = ETBExecutionBootstrapper(self.etb_config)
        cl_bootstrapper = ETBConsensusBootstrapper(self.etb_config)
        # set the bootstrap time and update the file. Then signal dockers via
        # checkpoint.
        self._write_bootstrap_genesis_time()
        self._write_checkpoint_file("etb-config-checkpoint-file")

        # signal the consensus bootnode is ready to come online.
        self._write_checkpoint_file("consensus-bootnode-checkpoint-file")

        # bootstrap all the execution clients.
        el_bootstrapper.bootstrap_execution_clients()
        self._write_checkpoint_file("execution-checkpoint-file")

        # pair all the EL clients together.
        self._pair_el_clients(self._get_all_el_enodes())

        # bootstrap all the consensus clients.
        cl_bootstrapper.bootstrap_consensus_clients()
        self._write_checkpoint_file("consensus-checkpoint-file")

    def clear_last_run(self):
        """
        Clear all the files and dirs present in the testnet-root.
        """
        testnet_root = self.etb_config.get("testnet-root")
        if Path(testnet_root).exists():
            for file in os.listdir(testnet_root):
                path = Path(os.path.join(testnet_root, file))
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()

    # General private helpers to keep functions short.
    def _write_docker_compose(self):
        """
        Write the docker-compose file to bring the testnet up for bootstrapping
        and running.
        """
        logger.info("Creating docker-compose file")
        docker_path = self.etb_config.get("docker-compose-file")
        docker_compose = generate_docker_compose(self.etb_config)
        with open(docker_path, "w") as f:
            yaml.safe_dump(docker_compose, f)

    def _write_consensus_bootnode_enr(self):
        """
        Populate the enr file to be used by the consensus bootnode.
        """
        # handle the consensus bootnode enr files:
        for name, cbc in self.etb_config.get("consensus-bootnodes").items():
            bootnode_path = Path(cbc.get("consensus-bootnode-enr-file"))
            bootnode_path.parents[0].mkdir(exist_ok=True)

    def _write_checkpoint_file(self, etb_config_checkpoint_path):
        """
        Write the checkpoint file to signal other containers that a checkpoint
        has been reached.
        """
        checkpoint_path = self.etb_config.get(etb_config_checkpoint_path)
        with open(checkpoint_path, "w") as etb_checkpoint:
            etb_checkpoint.write("1")

    def _write_bootstrap_genesis_time(self):
        """
        Take the current time and set that as bootstrap genesis in the etb-config.
        Write the updated etb-config file into the testnet dir.
        """
        self.etb_config.config["bootstrap-genesis"] = int(time.time())
        with open(self.etb_config.get("etb-config-file"), "w") as f:
            yaml.safe_dump(self.etb_config.config, f)

    def _get_all_el_enodes(self):
        """
        fetch the EL enodes for all clients that implement the admin RPC
        interface.

        returns: dict {client-name : enode,...}
        """

        etb_rpc = ETBExecutionRPC(self.etb_config, timeout=5)
        clients = self.etb_config.get_clients_with_el_admin_interface()
        node_info = etb_rpc.do_rpc_request(
            admin_node_info_RPC(), client_nodes=clients, all_clients=False
        )
        enodes = {}
        for name, info in node_info.items():
            enodes[name] = info["result"]["enode"]

        return enodes

    def _pair_el_clients(self, enode_dict, optional_delay=0):
        """
            Given a dict of enodes, iterate through it and pair the clients via
            the admin RPC interface.
        """
        etb_rpc = ETBExecutionRPC(self.etb_config, timeout=5)

        # iterate through all clients and enodes and peer them together.
        for client, enode in enode_dict.items():
            clients_to_peer = list(enode_dict.keys())
            # don't peer a client with itself.
            clients_to_peer.remove(client)
            etb_rpc.do_rpc_request(
                admin_add_peer_RPC(enode),
                client_nodes=clients_to_peer,
                all_clients=False,
            )
            time.sleep(optional_delay)