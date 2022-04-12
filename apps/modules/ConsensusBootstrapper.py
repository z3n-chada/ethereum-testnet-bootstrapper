import logging
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
