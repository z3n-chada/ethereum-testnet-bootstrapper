import argparse
import json
import os
import pathlib
import shutil
import time
import logging
import sys

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
    print(block)
    return block


def get_execution_bootstrapper_enode():

    etb_rpc = ETBExecutionRPC(global_config, timeout=60)
    bs_name = global_config.get("execution-bootstrapper")
    bs_node = f"{bs_name}-0"
    rpc = admin_node_info_RPC()
    responses = etb_rpc.do_rpc_request(rpc, [bs_node])
    node_info = responses[bs_node]["result"]
    print(node_info["enode"])
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

    e_checkpoint = global_config.get("execution-checkpoint-file")

    with open(e_checkpoint, "w", opener=rw_all_user) as f:
        f.write("1")

    enode = get_execution_bootstrapper_enode()
    print(f"bootstrapper writing enode: {enode}")
    with open("/data/local_testnet/execution-bootstrapper/enodes.txt", "w") as f:
        f.write(enode)


def generate_consensus_config():
    config = create_consensus_config(global_config)
    with open("/data/consensus-config.yaml", "w", opener=rw_all_user) as f:
        f.write(config)


def generate_consensus_genesis():

    global global_config
    latest_block = get_execution_bootstrapper_block()
    block_hash = latest_block["hash"][2:]
    block_time = latest_block["timestamp"]
    print(f"{block_hash} : {block_time}")
    preset_base = global_config.get("preset-base")
    deploy_consensus_genesis(global_config, block_hash, block_time, preset_base)
    generate_consensus_testnet_dirs(global_config)
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

    setup_environment()
    if not args.bootstrap_mode:
        generate_execution_genesis()
        generate_consensus_config()
        generate_consensus_genesis()
        link_all_execution_clients()
    if not args.no_docker_compose:
        write_docker_compose()


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

    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
    )
    logging.info("started the bootstrapper")
    args = parser.parse_args()
    bootstrap_testnet(args)
