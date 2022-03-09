import argparse
from ruamel import yaml
from web3.auto import w3
import subprocess
import pathlib
import time

"""
    Parses the config to get the settings for geth,
    then launches geth and obtains some private keys for
    sending messages, then starts the fuzzer.


    Required settings for the generic-module:
        action: "spam" //what action to take on the livefuzzer
        execution-config: whats the profile to use for geth

"""


def get_geth_bootnodes():
    enode_file = "/data/local_testnet/execution-bootstrapper/enodes.txt"
    while not pathlib.Path(enode_file).exists():
        time.sleep(1)
        print("waiting on bootnode")
    with open("/data/local_testnet/execution-bootstrapper/enodes.txt", "r") as f:
        enode = f.read()
    return enode.strip("\n")


def start_geth(ep):
    # geth init cmd
    gic = f"geth init --datadir /home/geth/ {ep['geth-genesis']}"
    print(f"transaction spammer: geth genesis launching: {gic}")
    x = subprocess.run(gic, shell=True, capture_output=True)
    # geth lauch cmd
    glc = "geth"
    glc += f" --bootnodes {get_geth_bootnodes()} --datadir /home/geth/"
    glc += f" --networkid {ep['network-id']} --port {ep['execution-http-port']}"
    glc += f" --http --http.api {ep['http-apis']} --http.addr 0.0.0.0"
    glc += ' --http.corsdomain "*" --keystore /source/apps/data/geth-keystores/'
    glc += " --rpc.allow-unprotected-txs"
    glc += f" --override.terminaltotaldifficulty={ep['terminalTotalDifficulty']}"
    glc += " --vmodule=rpc=5 &"
    print(f"transaction spammer: starting geth: {glc}", flush=True)
    subprocess.run(glc, shell=True)


def start_transaction_fuzzer(args):
    with open(args.config, "r") as f:
        gc = yaml.safe_load(f.read())

    execution_profile = gc["execution-configs"][
        gc["generic-modules"][args.module_name]["execution-config"]
    ]
    start_geth(execution_profile)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        dest="config",
        required=True,
        help="path to config file to consume for experiment",
    )

    parser.add_argument(
        "--module-name",
        dest="module_name",
        required=True,
        help="the name of this module in the generic-modules section",
    )

    args = parser.parse_args()
    start_transaction_fuzzer(args)
