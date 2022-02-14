"""
    Given CL slot times, deploy transactions to and from wallets.
"""
import pathlib
import random
import subprocess
import time

from ruamel import yaml
from web3.auto import w3

w3.eth.account.enable_unaudited_hdwallet_features()


def get_get_keypairs(config):
    k = {}
    mnemonic = config["accounts"]["eth1-account-mnemonic"]
    password = config["accounts"]["eth1-passphrase"]
    premines = config["accounts"]["eth1-premine"]
    for acc in premines:
        acct = w3.eth.account.from_mnemonic(
            mnemonic, account_path=acc, passphrase=password
        )
        k[acct.address] = acct.privateKey.hex()

    return k


def create_deposit_data(config, args):
    start_offset = args.start_offset
    num_deposits = args.num_deposits
    chain_id = config["config-params"]["deposit-chain-id"]
    validator_mnem = config["accounts"]["validator-mnemonic"]
    withdrawl_mnem = config["accounts"]["withdrawl-mnemonic"]
    cmd = (
        "eth2-val-tools deposit-data "
        + f"--source-min {start_offset} "
        + f"--source-max {start_offset + num_deposits} "
        + f"--fork-version {chain_id} "
        + f'--validators-mnemonic "{validator_mnem}" '
        + f'--withdrawals-mnemonic "{withdrawl_mnem}" '
        + "--as-json-list "
    )
    x = subprocess.run(cmd, shell=True, capture_output=True)
    stdout_deposit_data = x.stdout
    return stdout_deposit_data


def send_ethereal_beacon_deposit(deposit_address, data, pubkey, privkey, conn):
    cmd = (
        "ethereal beacon deposit "
        + "--allow-unknown-contract=True "
        + f'--address="{deposit_address}" '
        + '--data="/tmp/deposit_data" '
        + f'--from="{pubkey}" '
        + f'--privatekey="{privkey}" '
        + f'--connection="{conn}" '
        + "--debug "
        + "--wait"
    )

    print(subprocess.run(cmd, shell=True, capture_output=True))


def deploy_deposit(args):
    with open(args.config, "r") as f:
        gc = yaml.safe_load(f.read())

    deposit_data = create_deposit_data(gc, args)
    key_pairs = get_get_keypairs(gc)
    deposit_address = gc["config-params"]["deposit-contract-address"]

    # wrap ethereal with global_config.
    pubkey = random.choice(list(key_pairs.keys()))
    priv_key = key_pairs[pubkey]
    print(f"{pubkey} : {priv_key}")

    with open("/tmp/deposit_data", "wb") as f:
        f.write(deposit_data)

    # wait for the connection to exist.
    connection = pathlib.Path(args.geth_ipc)
    while not connection.exists():
        print("Waiting for geth ipc connection to open")
        time.sleep(1)

    send_ethereal_beacon_deposit(
        deposit_address,
        "/tmp/deposit_data",
        pubkey,
        priv_key,
        args.geth_ipc,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        dest="config",
        required=True,
        help="path to the scenario config to pull constants from",
    )
    parser.add_argument(
        "--geth-ipc",
        dest="geth_ipc",
        required=True,
        help="geth ipc endpoint to use for transactions",
    )
    parser.add_argument(
        "--start-offset",
        dest="start_offset",
        default=65,
        help="min source to pass to generate deposit-data",
    )
    parser.add_argument(
        "--num-deposits",
        dest="num_deposits",
        default=1,
        help="min source to pass to generate deposit-data",
    )

    args = parser.parse_args()
    deploy_deposit(args)
