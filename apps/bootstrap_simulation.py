import argparse
import time
import json
import ruamel.yaml as yaml
import pathlib
import shutil
import os

from modules.GethGenesis import create_geth_genesis
from modules.ConsensusConfig import create_consensus_config
from modules.ConsensusGenesis import deploy_consensus_genesis
from modules.TestnetGenerators import generate_consensus_testnet_dirs
from modules.DockerCompose import generate_docker_compose

global global_config


def rw_all_user(path, flag):
    return os.open(path, flag, 0o666)


def setup_environment():
    # clean up previous runs and remake the required directories.
    testnet_dir = pathlib.Path(global_config["files"]["testnet-dir"])
    if testnet_dir.exists():
        shutil.rmtree(str(testnet_dir))
    testnet_dir.mkdir()

    # remove all checkpoints
    e_checkpoint = global_config["files"]["execution-checkpoint"]
    c_checkpoint = global_config["files"]["consensus-checkpoint"]
    ec = pathlib.Path(e_checkpoint)
    cc = pathlib.Path(c_checkpoint)
    if ec.exists():
        ec.unlink()
    if cc.exists():
        cc.unlink()


def generate_execution_genesis():
    genesis = create_geth_genesis(global_config)
    genesis_file = global_config["files"]["geth-genesis"]
    e_checkpoint = global_config["files"]["execution-checkpoint"]
    with open(genesis_file, "w", opener=rw_all_user) as f:
        json.dump(genesis, f)
    with open(e_checkpoint, "w", opener=rw_all_user) as f:
        f.write("1")


def generate_consensus_config():
    config = create_consensus_config(global_config)
    with open("/data/consensus-config.yaml", "w", opener=rw_all_user) as f:
        f.write(config)


def generate_consensus_genesis():
    deploy_consensus_genesis(global_config)
    generate_consensus_testnet_dirs(global_config)
    c_checkpoint = global_config["files"]["consensus-checkpoint"]
    with open(c_checkpoint, "w", opener=rw_all_user) as f:
        f.write("1")


def write_docker_compose():
    dcyaml = generate_docker_compose(global_config)
    docker_compose = global_config["files"]["docker-compose"]
    with open(docker_compose, "w", opener=rw_all_user) as f:
        yaml.dump(dcyaml, f)


def bootstrap_testnet(args):
    global global_config
    with open(args.config, "r") as f:
        config = yaml.safe_load(f.read())

    global_config = config
    global_config["now"] = int(time.time())

    setup_environment()
    if not args.bootstrap_mode:
        generate_execution_genesis()
        generate_consensus_config()
        generate_consensus_genesis()
    if not args.no_docker_compose:
        write_docker_compose()


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

args = parser.parse_args()
bootstrap_testnet(args)
