"""
Spams the execution layer with transactions using the tx-fuzz tool.
see: https://github.com/MariusVanDerWijden/tx-fuzz
"""
import argparse
import logging
import pathlib
import random

from web3.auto import w3

from etb.common.utils import create_logger, PremineKey
from etb.config.etb_config import ETBConfig, ClientInstance, get_etb_config
from src.etb.monitoring.testnet_monitor import TestnetMonitor
from etb.interfaces.external.live_fuzzer import LiveFuzzer

w3.eth.account.enable_unaudited_hdwallet_features()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

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
        "--epoch-delay",
        dest="epoch_delay",
        type=int,
        default=None,
        help="what CL epoch to start spamming at",
    )

    parser.add_argument(
        "--tx-fuzz-path",
        dest="tx_fuzz_path",
        default="/usr/local/bin/tx-fuzz",  # defined in the etb-all-clients.Dockerfile
        help="path to the tx-fuzz binary",
    )

    parser.add_argument(
        "--log-level",
        dest="log_level",
        default="info",
        help="log level to use",
    )

    args = parser.parse_args()

    create_logger(name="tx-fuzz", log_level=args.log_level)
    etb_config: ETBConfig = get_etb_config()
    testnet_monitor = TestnetMonitor(etb_config)

    live_fuzzer_interface = LiveFuzzer(binary_path=pathlib.Path(args.tx_fuzz_path))

    # process args.
    if args.target_ip is None or args.target_port is None:
        client: ClientInstance = random.choice(etb_config.get_client_instances())
        args.target_ip = client.get_ip_address()
        args.target_port = client.execution_config.http_port

    rpc_path = f"http://{args.target_ip}:{args.target_port}"

    # get the private keys to use.
    mnemonic = etb_config.testnet_config.execution_layer.account_mnemonic
    account_pass = etb_config.testnet_config.execution_layer.keystore_passphrase
    premine_accts = etb_config.testnet_config.execution_layer.premines

    private_keys = []
    for acc in premine_accts:
        private_keys.append(
            PremineKey(
                mnemonic=mnemonic, account=acc, passphrase=account_pass
            ).private_key
        )

    logging.debug(f"private keys: {private_keys}")

    logging.info(f"Waiting for start epoch {args.epoch_delay}")
    testnet_monitor.wait_for_epoch(args.epoch_delay)

    live_fuzzer_interface.start_fuzzer(
        rpc_path=rpc_path,
        fuzz_mode=args.fuzz_mode,
        private_key=random.choice(private_keys),
    )
