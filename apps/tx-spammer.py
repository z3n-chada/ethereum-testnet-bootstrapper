"""
    Meant to launch tx-fuzz: https://github.com/MariusVanDerWijden/tx-fuzz
    Usage: ./tx-fuzz.bin --rpc RPC_IP:RPC_URL COMMAND (spam) --pk "comma,seperated,private,keys" --seed RAND_SEED
"""
import argparse
import logging
import os
import random
import time
import subprocess

from web3.auto import w3
from pathlib import Path

from modules.UtilityWrappers import create_logger
from modules.TestnetMonitor import TestnetMonitor
from modules.ETBConfig import ETBConfig, ClientInstance

w3.eth.account.enable_unaudited_hdwallet_features()


class TxFuzz(object):
    """
    Class to represent a livefuzzer instance.
    """

    def __init__(self, etb_config,
                 logger: logging.Logger = None,
                 target_ip: str = None,
                 target_port: int = None,
                 fuzz_mode: str = "spam",
                 start_slot: int = None,
                 fuzzer_path: str = "/usr/local/bin/livefuzzer",
                 ):
        """
            :param etb_config: ETBConfig object
            :param logger: logger to use or construct one if None
            :param target_ip: ip address of the client instance to submit txs to
            :param target_port: rpc-port of the client instance to submit txs to
            :param fuzz_mode: mode to run tx-fuzz in (spam by default)
            :param start_slot: CL slot to start the livefuzzer at (default to 2nd epoch)
            :param fuzzer_path: path to the livefuzzer binary (default: /usr/local/bin/livefuzzer)
        """

        if logger is None:
            self.logger = logging.getLogger()
        else:
            self.logger = logger
        self.etb_config: ETBConfig = etb_config
        self.testnet_monitor = TestnetMonitor(self.etb_config, logger=logger)
        # grab the client instance to attach to.
        if target_ip is None or target_port is None:
            client: ClientInstance = random.choice(self.etb_config.get_client_instances())
            self.target_ip = client.get_ip_address()
            self.target_port = client.get("execution-http-port")
        else:
            self.target_ip = target_ip
            self.target_port = target_port

        if start_slot is None:
            self.start_slot = self.etb_config.epoch_to_slot(2)
        else:
            self.start_slot = start_slot

        self.fuzz_mode = fuzz_mode
        self.fuzzer_path = fuzzer_path
        self.logger.info("tx-fuzzer initialized with the following parameters:")
        self.logger.info(f"execution client: {self.target_ip}:{self.target_ip}")
        self.logger.info(f"start slot: {self.start_slot}")
        self.logger.info(f"fuzz mode: {self.fuzz_mode}")
        self.logger.info(f"fuzzer path: {self.fuzzer_path}")

    def get_keys(self):
        pub_keys = []
        priv_keys = []
        for pkp in self.etb_config.get_premine_keypairs():
            pub_keys.append(pkp.public_key)
            priv_keys.append(pkp.private_key)
        return pub_keys, priv_keys

    def launch_tx_fuzzer(self):
        _, private_keys = self.get_keys()

        cmd = [
            self.fuzzer_path,
            self.fuzz_mode,
            "--rpc",
            f"http://{self.target_ip}:{self.target_port}",
            "--sk",
            ",".join(private_keys),
        ]

        self.testnet_monitor.wait_for_slot(self.start_slot)
        self.logger.info("starting tx-fuzzer")
        self.logger.debug(f"{cmd}")
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

    args = parser.parse_args()

    logger = create_logger("tx-fuzz", "debug")
    etb_config = ETBConfig(args.config, logger)

    if args.seed is not None:
        logger.info(f"Using user supplied random seed: {args.seed}")
        random.seed(args.seed)

    else:
        rand = os.urandom(10)
        seed = int.from_bytes(rand, "big")
        logger.info(f"setting random seed to: {seed}")
        random.seed(seed)

    tfl = TxFuzz(etb_config,
                 target_ip=args.target_ip,
                 target_port=args.target_port,
                 fuzz_mode=args.fuzz_mode,
                 start_slot=args.start_slot,
                 fuzzer_path=args.tx_fuzz_path,
                 logger=logger)

    tfl.launch_tx_fuzzer()
