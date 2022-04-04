import argparse
import json
import os
import pathlib
import shutil
import time
import logging
import sys
import random

import ruamel.yaml as yaml

from modules.ConsensusConfig import create_consensus_config
from modules.ConsensusGenesis import deploy_consensus_genesis
from modules.DockerCompose import generate_docker_compose

from modules.ExecutionGenesis import ExecutionGenesisWriter
from modules.GethIPCUtils import GethIPC

from modules.TestnetGenerators import generate_consensus_testnet_dirs
from modules.ETBConfig import ETBConfig
from modules.ExecutionRPC import (
    ETBExecutionRPC,
    admin_add_peer_RPC,
    admin_node_info_RPC,
    eth_get_block_RPC,
)

global global_config
global logger


def rw_all_user(path, flag):
    return os.open(path, flag, 0o666)


def get_execution_bootstrapper_block():
    # get the bootstrapper and ask for the latest block.
    etb_rpc = ETBExecutionRPC(global_config, timeout=60)
    bs_name = global_config.get("execution-bootstrapper")
    bs_node = f"{bs_name}-0"
    rpc = eth_get_block_RPC()
    responses = etb_rpc.do_rpc_request(rpc, [bs_node])
    block = responses[bs_node]["result"]
    logger.info(f"execution_bootstrapper_block: {block}")
    return block


def get_execution_bootstrapper_enode():

    etb_rpc = ETBExecutionRPC(global_config, timeout=60)
    bs_name = global_config.get("execution-bootstrapper")
    bs_node = f"{bs_name}-0"
    rpc = admin_node_info_RPC()
    responses = etb_rpc.do_rpc_request(rpc, [bs_node])
    node_info = responses[bs_node]["result"]
    logger.info(f"boostrapper enode: {node_info['enode']}")
    return node_info["enode"]


def setup_environment():
    # clean up previous runs and remake the required directories.
    testnet_dir = pathlib.Path(global_config.get("testnet-dir"))
    if testnet_dir.exists():
        shutil.rmtree(str(testnet_dir))
    testnet_dir.mkdir()

    # we want a clean genesis each time we run the bootstrapper.
    execution_bootstrapper_dir = pathlib.Path(
        global_config.get("execution-bootstrap-dir")
    )

    if execution_bootstrapper_dir.exists():
        shutil.rmtree(str(execution_bootstrapper_dir))
        # "/data/execution-bootstrapper"

    # remove all checkpoints
    e_checkpoint = global_config.get("execution-checkpoint-file")
    c_checkpoint = global_config.get("consensus-checkpoint-file")
    ec = pathlib.Path(e_checkpoint)
    cc = pathlib.Path(c_checkpoint)
    if ec.exists():
        ec.unlink()
    if cc.exists():
        cc.unlink()


def generate_execution_genesis():
    egw = ExecutionGenesisWriter(global_config)
    logger.debug("Creating execution genesis files.")
    # geth first
    geth_genesis_path = global_config.get("geth-genesis-file")
    geth_genesis = egw.create_geth_genesis()
    with open(geth_genesis_path, "w", opener=rw_all_user) as f:
        json.dump(geth_genesis, f)

    besu_genesis_path = global_config.get("besu-genesis-file")
    besu_genesis = egw.create_besu_genesis()
    with open(besu_genesis_path, "w", opener=rw_all_user) as f:
        json.dump(besu_genesis, f)

    nethermind_genesis_path = global_config.get("nethermind-genesis-file")
    nethermind_genesis = egw.create_nethermind_genesis()
    with open(nethermind_genesis_path, "w", opener=rw_all_user) as f:
        json.dump(nethermind_genesis, f)

    # before we are done add the execution client jwt.
    for name, ec in global_config.get("execution-clients").items():
        if ec.has("jwt-secret-file"):
            for node in range(ec.get("num-nodes")):
                jwt_secret = f"0x{random.randbytes(32).hex()}"
                jwt_secret_file = ec.get("jwt-secret-file", node)
                with open(jwt_secret_file, "w") as f:
                    f.write(jwt_secret)

    e_checkpoint = global_config.get("execution-checkpoint-file")

    with open(e_checkpoint, "w", opener=rw_all_user) as f:
        f.write("1")

    # no default enode for now.
    # enode = get_execution_bootstrapper_enode()
    # with open("/data/local_testnet/execution-bootstrapper/enodes.txt", "w") as f:
    #     f.write(enode)


def generate_consensus_config():
    config = create_consensus_config(global_config)
    logger.debug("Creating consensus config file.")
    with open("/data/consensus-config.yaml", "w", opener=rw_all_user) as f:
        f.write(config)


def generate_consensus_genesis():

    global global_config
    latest_block = get_execution_bootstrapper_block()
    block_hash = latest_block["hash"][2:]
    block_time = latest_block["timestamp"]
    logger.info(f"{block_hash} : {block_time}")
    preset_base = global_config.get("preset-base")
    deploy_consensus_genesis(global_config, block_hash, block_time, preset_base)
    generate_consensus_testnet_dirs(global_config)

    # before we are done we need to write the jwt-secret files if they use them.
    for name, cc in global_config.get("consensus-clients").items():
        if cc.has("jwt-secret-file"):
            for node in range(cc.get("num-nodes")):
                jwt_secret = f"0x{random.randbytes(32).hex()}"
                jwt_secret_file = cc.get("jwt-secret-file", node)
                with open(jwt_secret_file, "w") as f:
                    f.write(jwt_secret)

    c_checkpoint = global_config.get("consensus-checkpoint-file")
    with open(c_checkpoint, "w", opener=rw_all_user) as f:
        f.write("1")


def write_docker_compose():
    dcyaml = generate_docker_compose(global_config)
    docker_compose = global_config.get("docker-compose-file")
    with open(docker_compose, "w", opener=rw_all_user) as f:
        yaml.dump(dcyaml, f)


def link_all_execution_clients():
    # currently we don't have a working eth1 bootnode. So we do this manually.

    # Includes the bootstrapper, and all consensus client execution endpoints

    etb_rpc = ETBExecutionRPC(global_config, timeout=60)
    node_info = etb_rpc.do_rpc_request(admin_node_info_RPC(), all_clients=True)

    enodes = {}
    for name, info in node_info.items():
        enodes[name] = info["result"]["enode"]

    for enode in enodes.values():
        etb_rpc.do_rpc_request(admin_add_peer_RPC(enode), all_clients=True)


def bootstrap_testnet(args):
    global global_config

    global_config = ETBConfig(args.config)

    global_config.now = int(time.time())

    create_logger(args)

    setup_environment()
    if not args.bootstrap_mode:
        logging.info("bootstrapper creating testnet.")
        generate_execution_genesis()
        generate_consensus_config()
        generate_consensus_genesis()
        link_all_execution_clients()
    if not args.no_docker_compose:
        write_docker_compose()
        logging.info("bootstrapper --bootstrap-mode: created docker-compose")


def create_logger(args):
    global logger
    logging_levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "critical": logging.CRITICAL,
        "error": logging.ERROR,
        "warning": logging.WARNING,
    }
    if args.log_level.lower() not in logging_levels:
        raise Exception(f"Got bad logging level: {args.log_level}")

    log_level = logging_levels[args.log_level.lower()]
    log_format = logging.Formatter("%(asctime)s: %(levelname)s: %(message)s")
    logger = logging.getLogger("bootstrapper_log")
    logger.setLevel(log_level)

    # logging.basicConfig(format=log_format, level=log_level)

    if args.log_to_stdout:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(log_level)
        stdout_handler.setFormatter(log_format)
        logger.addHandler(stdout_handler)
    if args.log_to_file:
        file_handler = logging.FileHandler(args.log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)

    logger.info("started the bootstrapper")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config", dest="config", required=True, help="path to config to consume"
    )

    parser.add_argument(
        "--no-docker-compose",
        dest="no_docker_compose",
        action="store_true",
        help="Skip outputting a docker-compose.yaml",
    )

    parser.add_argument(
        "--bootstrap-mode",
        dest="bootstrap_mode",
        action="store_true",
        help="Just create the docker-compose script which bootstraps and runs the network.",
    )

    parser.add_argument(
        "--log-to-stdout",
        dest="log_to_stdout",
        action="store_true",
        default=True,
        help="add a log stream handler for stdout.",
    )

    parser.add_argument(
        "--log-to-file",
        dest="log_to_file",
        action="store_true",
        default=True,
        help="add a log stream handler for a file.",
    )

    parser.add_argument(
        "--log-file",
        dest="log_file",
        default="/source/data/bootstrapper.log",
        help="Log file destination for the bootstrapper.",
    )

    parser.add_argument(
        "--log-level",
        dest="log_level",
        default="debug",
        help="logging level to use.",
    )

    args = parser.parse_args()
    bootstrap_testnet(args)
