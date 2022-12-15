import logging
from pathlib import Path
from .ConsensusDirectoryGenerator import generate_consensus_dirs
from .ConsensusGenesis import ConsensusGenesisWriter
from .ExecutionRPC import ETBExecutionRPC, eth_get_block_RPC
import json
import random

logger = logging.getLogger("bootstrapper_log")


class ETBConsensusBootstrapper(object):
    """
    This bootstrapper is for the consensus clients.
    """

    def __init__(self, etb_config):
        self.etb_config = etb_config

    def create_consensus_dirs(self):
        """
        This method creates all the directories in the local testnet dir
        that will be used by consensus clients. Additionally, if a CL client
        has its own execution client it will create that as well.
        """

        logger.info("Creating consensus client directories")
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

    def create_consensus_client_jwt(self):
        """
        This method parses the etb-config and creates jwt-secret files for all
        consensus clients that use it.
        """
        for items, cc in self.etb_config.get("consensus-clients").items():
            if cc.has("jwt-secret-file"):
                for node in range(cc.get("num-nodes")):
                    jwt_secret = f"0x{random.randbytes(32).hex()}"
                    jwt_secret_file = cc.get("jwt-secret-file", node)
                    with open(jwt_secret_file, "w") as f:
                        f.write(jwt_secret)

    def bootstrap_consensus_clients(self):
        # genesis config
        logger.info("ConsensusBootstrapper creating consensus config.yaml")
        consensus_genesis_writer = ConsensusGenesisWriter(self.etb_config)
        consensus_config = consensus_genesis_writer.create_consensus_config()
        with open(self.etb_config.get("consensus-config-file"), "w") as f:
            f.write(consensus_config)
        logger.debug("ConsensusBootstrapper wrote config.yaml")

        # genesis ssz.. This requires eth1 block hash and time.
        logger.info("ConsensusBootstrapper creating consensus genesis.ssz")
        etb_rpc = ETBExecutionRPC(self.etb_config, timeout=60, non_error=True)
        rpc = eth_get_block_RPC()
        bootstrapper_base_name = self.etb_config.get("execution-bootstrapper")
        bootstrapper = f"{bootstrapper_base_name}-0"

        responses = etb_rpc.do_rpc_request(rpc, [bootstrapper])
        block = responses[bootstrapper]["result"]
        logger.debug(f"ConsensusBootstrapper got execution block: {block}")
        block_hash = block["hash"][2:]
        block_time = block["timestamp"]
        genesis_ssz = consensus_genesis_writer.create_consensus_genesis(
            eth1_block_hash=block_hash, eth1_timestamp=block_time
        )
        with open(self.etb_config.get("consensus-genesis-file"), "wb") as f:
            f.write(genesis_ssz)
        logger.debug("ConsensusBootstrapper wrote genesis.ssz")

        generate_consensus_dirs(self.etb_config)
