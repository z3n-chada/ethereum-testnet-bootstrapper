"""
    Python wrapper meant to be used with the kurtosis tx-fuzz docker.
    The modified tx-fuzzer uses the following args:

    ./tx-fuzz.bin RPC_IP:RPC_URL command (spam) "comma,seperated,private,keys" "comma,seperated,addresses"
"""
import argparse
import logging
import os
import random
import time
import subprocess

from web3.auto import w3
from pathlib import Path

from modules.ETBUtils import create_logger
from modules.TestnetMonitor import TestnetMonitor
from modules.ETBConfig import ETBConfig, ClientInstance

w3.eth.account.enable_unaudited_hdwallet_features()


class TxFuzzer(object):
    def __init__(self, etb_config,
                 logger: logging.Logger = None,
                 target_ip: str = None,
                 target_port: int = None,
                 fuzz_mode: str = "spam",
                 start_slot: int = None,
                 fuzzer_path: str = "/usr/local/bin/tx-fuzz",
                 ):

        if logger is None:
            self.logger = logging.getLogger()
        else:
            self.logger = logger
        self.etb_config: ETBConfig = etb_config
        self.testnet_monitor = TestnetMonitor(self.etb_config, logger=logger)
        if target_ip is None or target_port is None:
            client: ClientInstance = random.choice(self.etb_config.get_client_instances())
            self.target_ip = client.get_ip_address()
            self.target_port = client.get("execution-http-port")
            self.logger.info(f"Using random client for tx-fuzz: {self.target_ip}:{self.target_port}")
        else:
            self.target_ip = target_ip
            self.target_port = target_port
            self.logger.info(f"Using supplied client for tx-fuzz: {self.target_ip}:{self.target_port}")
        if start_slot is None:
            # somewhere between 2 and 4 epochs
            self.start_slot = random.randint(self.etb_config.epoch_to_slot(2), self.etb_config.epoch_to_slot(4))
            self.logger.info(f"Using random start slot for tx-fuzz: {self.start_slot}")
        else:
            self.start_slot = start_slot
            self.logger.info(f"Using supplied start slot for tx-fuzz: {self.start_slot}")

        self.fuzz_mode = fuzz_mode
        self.fuzzer_path = fuzzer_path

    def get_keys(self):
        pub_keys = []
        priv_keys = []
        for pkp in self.etb_config.get_premine_keypairs():
            pub_keys.append(pkp.public_key)
            priv_keys.append(pkp.private_key)
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

        self.testnet_monitor.wait_for_slot(self.start_slot)
        self.logger.info(f"tx-fuzzer launching: {cmd}")
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
        default=None,
        required=False,
        help="target ip address to use for spamming",
    )

    parser.add_argument(
        "--target-port",
        dest="target_port",
        default=None,
        type=int,
        required=False,
        help="target port to use for spamming",
    )

    parser.add_argument(
        "--slot-delay",
        dest="start_slot",
        type=int,
        default=None,
        help="what slot to start spamming at",
    )

    parser.add_argument(
        "--tx-fuzz-path",
        dest="tx_fuzz_path",
        default="/usr/local/bin/tx-fuzz",  # defined in the etb-all-clients.Dockerfile
        help="path to the tx-fuzz binary",
    )

    parser.add_argument(
        "--seed",
        dest="seed",
        default=None,
        help="seed to use for random number generation.",
    )

    while not Path("/data/etb-config-file-ready").exists():
        print("tx-fuzzer waiting for etb-config to become available.")
        time.sleep(1)

    _args = parser.parse_args()

    _logger = create_logger("tx-fuzz", "debug")
    _etb_config = ETBConfig(_args.config, _logger)

    if _args.seed is not None:
        _logger.info(f"Using user supplied random seed: {_args.seed}")
        random.seed(_args.seed)

    else:
        rand = os.urandom(10)
        seed = int.from_bytes(rand, "big")
        _logger.info(f"setting random seed to: {seed}")
        random.seed(seed)

    tfl = TxFuzzer(_etb_config,
                   target_ip=_args.target_ip,
                   target_port=_args.target_port,
                   fuzz_mode=_args.fuzz_mode,
                   start_slot=_args.start_slot,
                   fuzzer_path=_args.tx_fuzz_path,
                   logger=_logger)

    tfl.launch_tx_fuzzer()
