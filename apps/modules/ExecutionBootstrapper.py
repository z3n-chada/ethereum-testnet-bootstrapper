"""
    Stores all fo the logic and methods required to bootstrap all the execution clients used
    in an experiment/local testnet.
"""
import json
import logging
import random
from pathlib import Path
import subprocess

from .ETBConfig import ExecutionClient
from .ExecutionGenesis import ExecutionGenesisWriter

logger = logging.getLogger("bootstrapper_log")


class ETBExecutionBootstrapper(object):
    """
    This bootstrapper is responsible for setting up all the
    execution clients. (including consensus local execution clients)
    """

    def __init__(self, etb_config):
        self.etb_config = etb_config

    def bootstrap_execution_clients(self):
        """
        The execution bootstrap phase consists of writing every EL's genesis
        json file in their respective dirs.
        """
        logger.info("ExecutionBootstrapper started.")
        self.write_all_execution_genesis_files()
        logger.info("ExecutionBootstrapper: all execution genesis files written")

    def create_execution_client_jwt(self):
        """
        For all the execution clients we are doing an init for, check to see if
        they use jwt-secrets, if they do go ahead and create them.
        """
        for name, ec in self.etb_config.get("execution-clients").items():
            if ec.has("jwt-secret-file"):
                for node in range(ec.get("num-nodes")):
                    jwt_secret = f"0x{random.randbytes(32).hex()}"
                    jwt_secret_file = ec.get("jwt-secret-file", node)
                    with open(jwt_secret_file, "w") as f:
                        f.write(jwt_secret)

    def create_stand_alone_execution_dirs(self):
        """
        For execution clients they may be stand-alone or consensus paired. A stand-alone client
        is one that the docker instance running it only has the execution client running, v.s. a
        paired client which has both a consensus and execution client. This method creates the dirs
        used by all stand-alone execution clients.
        """
        logger.info("Creating stand-alone execution client directories")
        for name, ec in self.etb_config.get("execution-clients").items():
            Path(ec.get("execution-data-dir")).mkdir()

    def write_all_execution_genesis_files(self):
        """
        This method creates all the execution genesis files for the clients we support.
        The genesis files are created and written to the file specified by the etb-CLIENT-genesis-file
        """
        egw = ExecutionGenesisWriter(self.etb_config)
        logger.debug("Creating execution genesis files.")
        # geth first
        geth_genesis_path = self.etb_config.get("geth-genesis-file")
        geth_genesis = egw.create_geth_genesis()
        with open(geth_genesis_path, "w") as f:
            json.dump(geth_genesis, f)

        besu_genesis_path = self.etb_config.get("besu-genesis-file")
        besu_genesis = egw.create_besu_genesis()
        with open(besu_genesis_path, "w") as f:
            json.dump(besu_genesis, f)

        nethermind_genesis_path = self.etb_config.get("nether-mind-genesis-file")
        nethermind_genesis = egw.create_nethermind_genesis()
        with open(nethermind_genesis_path, "w") as f:
            json.dump(nethermind_genesis, f)
