"""
    Python wrapper meant to be used with the kurtosis tx-fuzz docker.
    The modified tx-fuzzer uses the following args:

    ./tx-fuzz.bin RPC_IP:RPC_URL command (spam) "comma,seperated,private,keys" "comma,seperated,addresses"
"""

import json
from ruamel import yaml
from web3.auto import w3

w3.eth.account.enable_unaudited_hdwallet_features()


def get_keys(config_path):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f.read())

    mnemonic = config["accounts"]["eth1-account-mnemonic"]
    passphrase = config["accounts"]["eth1-passphrase"]
    premines = config["accounts"]["eth1-premine"]

    keys = {}
    for acc in premines:
        acct = w3.eth.account.from_mnemonic(
            mnemonic, account_path=acc, passphrase=passphrase
        )
        pub = acct.address
        priv = acct.privateKey.hex()
        keys[pub] = priv

    return keys


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
        "--action",
        dest="action",
        required=True,
        help="{publicKeys/privateKeys}",
    )

    args = parser.parse_args()

    keys = get_keys(args.config)

    if args.action == "publicKeys":
        print(",".join(keys.keys()))

    elif args.action == "privateKeys":
        print(",".join(keys.values()))

    else:
        raise Exception("action can only be publicKeys or privateKeys")
