import argparse
import logging
import sys

from modules.TestnetBootstrapper import EthereumTestnetBootstrapper
from modules.UtilityWrappers import create_logger

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        dest="config",
        required=True,
        help="Which config file to use to create a testnet.",
    )

    parser.add_argument(
        "--clear-last-run",
        dest="clear_last_run",
        action="store_true",
        default=False,
        help="Clear the last run.",
    )

    parser.add_argument(
        "--init-testnet",
        dest="init_testnet",
        action="store_true",
        default=False,
        help="Initialize the testnet to be bootstrapped.",
    )

    parser.add_argument(
        "--bootstrap-testnet",
        dest="bootstrap_testnet",
        action="store_true",
        default=False,
        help="Start the testnet",
    )

    parser.add_argument(
        "--log-level",
        dest="log_level",
        default="debug",
        help="logging level to use.",
    )

    args = parser.parse_args()
    logger = create_logger("testnet_bootstrapper", args.log_level)
    etb = EthereumTestnetBootstrapper(args.config, logger)

    if args.clear_last_run:
        etb.clear_last_run()
        logger.debug("testnet_bootstrapper has finished cleaning up.")

    if args.init_testnet:
        etb.init_testnet()
        logger.debug("testnet_bootstrapper has finished init-ing the testnet.")

    if args.bootstrap_testnet:
        etb.bootstrap_testnet()
        logger.debug("testnet_bootstrapper has finished bootstrapping the testnet.")
