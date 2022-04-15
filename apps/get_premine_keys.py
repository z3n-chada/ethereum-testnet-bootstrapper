"""
    ./tx-fuzz.bin RPC_IP:RPC_URL command (spam) "comma,seperated,private,keys" "comma,seperated,addresses"
"""

from modules.ETBConfig import ETBConfig


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        dest="config",
        required=True,
        help="path to config file to consume for experiment",
    )
    args = parser.parse_args()

    etb_config = ETBConfig(args.config)
    premine_keys = etb_config.get("premine-keys")
    priv_keys = [k for k in premine_keys.values()]
    pub_keys = [k for k in premine_keys.keys()]
    print(f"Premine keys: {premine_keys}")
    # some launchers need private and public key lists, put them here
    # so it is easy to copy and paste.
    print(f"Premine private keys: {priv_keys}")
    print(f"Premine public keys: {pub_keys}")
