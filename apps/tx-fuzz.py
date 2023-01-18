"""
    Python wrapper meant to be used with the kurtosis tx-fuzz docker.
    The modified tx-fuzzer uses the following args:

    ./tx-fuzz.bin RPC_IP:RPC_URL command (spam) "comma,seperated,private,keys" "comma,seperated,addresses"
"""
import argparse
import time
import subprocess

from web3.auto import w3
from pathlib import Path
from modules.ETBConfig import ETBConfig



w3.eth.account.enable_unaudited_hdwallet_features()


class TxFuzzLauncher(object):
    def __init__(self, args):
        self.etb_config = ETBConfig(args.config)
        self.target_ip = args.target_ip
        self.target_port = args.target_port
        self.fuzz_mode = args.fuzz_mode
        self.fuzz_delay = args.fuzz_delay
        self.fuzzer_path = args.tx_fuzz_path

    def get_keys(self):
        """
        Gets the keys for all defined premines
        :return: [public-keys], [private-keys]
        """

        mnemonic = self.etb_config.get("eth1-account-mnemonic")
        passphrase = self.etb_config.get("eth1-passphrase")
        premines = self.etb_config.global_config['accounts']['eth1-premine'].keys()

        pub_keys = []
        priv_keys = []

        for acc in premines:
            acct = w3.eth.account.from_mnemonic(
                mnemonic, account_path=acc, passphrase=passphrase
            )
            pub_keys.append(acct.address)
            priv_keys.append(acct.privateKey.hex())

        return pub_keys, priv_keys

    def launch_tx_fuzzer(self):
        public_keys, private_keys = self.get_keys()

        cmd = [
            self.fuzzer_path,
            f"http://{self.target_ip}:{self.target_port}",
            self.fuzz_mode,
            ",".join(private_keys),
            ",".join(public_keys),
        ]

        launch_time = self.etb_config.get('bootstrap-genesis')
        now = int(time.time())
        if now > (launch_time + self.fuzz_delay):
            fuzzer_wait = 0
        else:
            fuzzer_wait = (launch_time + self.fuzz_delay) - now

        print(f"tx-fuzz waiting: {fuzzer_wait}")
        time.sleep(fuzzer_wait)

        print(f"tx-fuzzer launching: {cmd}")
        subprocess.run(cmd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        dest="config",
        required=True,
        help="path to config file to consume for experiment",
    )

    parser.add_argument(
        "--fuzz-mode",
        dest="fuzz_mode",
        default="spam",
        help="tx-fuzz mode to use",
    )

    parser.add_argument(
        "--target-ip",
        dest="target_ip",
        required=True,
        help="target ip address to use for spamming",
    )

    parser.add_argument(
        "--target-port",
        dest="target_port",
        required=True,
        help="target port to use for spamming",
    )

    parser.add_argument(
        "--tx-fuzz-delay",
        dest="fuzz_delay",
        type=int,
        default=30,
        help="how long to wait in seconds before spamming",
    )

    parser.add_argument(
        "--tx-fuzz-path",
        dest="tx_fuzz_path",
        default="/usr/local/bin/tx-fuzz",  # defined in the etb-all-clients.Dockerfile
        help="path to the tx-fuzz binary",
    )

    while not Path("/data/etb-config-file-ready").exists():
        print("tx-fuzzer waiting for etb-config to become available.")
        time.sleep(1)

    args = parser.parse_args()
    tfl = TxFuzzLauncher(args)
    tfl.launch_tx_fuzzer()
