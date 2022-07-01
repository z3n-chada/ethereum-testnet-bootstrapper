import json
import logging
import random
import subprocess

from .ETBConfig import ExecutionClient
from .ExecutionGenesis import ExecutionGenesisWriter

logger = logging.getLogger("bootstrapper_log")


class ETBExecutionBootstrapper(object):
    """
    This bootstrapper is responsible for setting up all of the
    execution clients. (including consensus local execution clients)
    """

    def __init__(self, etb_config):
        self.etb_config = etb_config

    def bootstrap_execution_clients(self):
        """
        In order to bootstrap we must generate genesis.ssz and
        the config files for each of the clients.
        """
        logger.info("ExecutionBootstrapper started.")

        self.write_all_execution_genesis_files()

        logger.info("ExecutionBootstrapper: all execution genesis files written")

    def create_execution_client_jwt(self):
        for name, ec in self.etb_config.get("execution-clients").items():
            if ec.has("jwt-secret-file"):
                for node in range(ec.get("num-nodes")):
                    jwt_secret = f"0x{random.randbytes(32).hex()}"
                    jwt_secret_file = ec.get("jwt-secret-file", node)
                    with open(jwt_secret_file, "w") as f:
                        f.write(jwt_secret)

    def create_erigon_nodekey_files(self):
        for name, ec in self.etb_config.get("execution-clients").items():
            if ec.get("client") == "erigon":
                for node in range(ec.get("num-nodes")):
                    with open(
                        f"{ec.get_execution_data_dir(node)}/nodekey.txt", "w"
                    ) as f:
                        f.write(f"{hex(random.getrandbits(32*8))[2:].zfill(64)}")

        for name, cc in self.etb_config.get("consensus-clients").items():
            if cc.has("local-execution-client") and cc.get("local-execution-client"):
                for node in range(cc.get("num-nodes")):
                    if cc.execution_config.get("client") == "erigon":
                        with open(
                            f"{cc.get_execution_data_dir(node)}/nodekey.txt", "w"
                        ) as f:
                            f.write(f"{hex(random.getrandbits(32*8))[2:].zfill(64)}")

    def get_erigon_enodes(self):
        enodes = []
        for name, ec in self.etb_config.get("execution-clients").items():
            if ec.get("client") == "erigon":
                for node in range(ec.get("num-nodes")):
                    with open(
                        f"{ec.get_execution_data_dir(node)}/nodekey.txt", "r"
                    ) as f:
                        nodekey = f.read()
                    cmd = [
                        "bootnode",
                        "--nodekeyhex",
                        f"{nodekey}",
                        "--writeaddress",
                    ]

                    out = subprocess.run(cmd, capture_output=True)
                    enode = out.stdout.decode("utf-8").strip()
                    ip = cc.get("ip-addr", node)
                    p2p_port = cc.execution_config.get("execution-p2p-port")
                    enodes.append(f"{enode}@{ip}:{p2p_port}")

        for name, cc in self.etb_config.get("consensus-clients").items():
            if cc.has("local-execution-client") and cc.get("local-execution-client"):
                for node in range(cc.get("num-nodes")):
                    if cc.execution_config.get("client") == "erigon":
                        with open(
                            f"{cc.get_execution_data_dir(node)}/nodekey.txt", "r"
                        ) as f:
                            nodekey = f.read()

                        # turn the nodekey into enode
                        cmd = [
                            "bootnode",
                            "--nodekeyhex",
                            f"{nodekey}",
                            "--writeaddress",
                        ]

                        out = subprocess.run(cmd, capture_output=True)
                        enode = out.stdout.decode("utf-8").strip()
                        ip = cc.get("ip-addr", node)
                        p2p_port = cc.execution_config.get("execution-p2p-port")
                        enodes.append(f"enode://{enode}@{ip}:{p2p_port}")
        return enodes

    def write_all_execution_genesis_files(self):
        """
        Here we create the genesis.json files that the execution
        clients use for genesis.
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

        # nethermind is picky..
        # add erigon genesis for new fields for their genesis.
        erigon_genesis_path = self.etb_config.get("erigon-genesis-file")
        erigon_genesis = egw.create_erigon_genesis()
        with open(erigon_genesis_path, "w") as f:
            json.dump(erigon_genesis, f)
