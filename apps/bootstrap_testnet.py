import argparse
import pathlib

from modules.Utils import logging_levels, get_logger
from modules.TestnetBootstrapper import EthereumTestnetBootstrapper

logger = get_logger(log_level="debug", name="testnet_bootstrapper")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        dest="config",
        required=False,
        help="Which config file to use to create a testnet.",
    )

    parser.add_argument(
        "--clean",
        dest="clean",
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

    if args.log_level not in logging_levels:
        raise ValueError(f"Invalid logging level: {args.log_level} ({logging_levels.keys()})")
    logger.setLevel(args.log_level.upper())
    logger.info("testnet_bootstrapper has started.")

    etb = EthereumTestnetBootstrapper(logger=logger)

    if args.clean:
        etb.clean()
        logger.debug("testnet_bootstrapper has finished cleaning up.")

    if args.init_testnet:
        # make sure we are going from source.
        if args.config.split("/")[0] != "source":
            logger.debug("prepending source to the config path in order to map in the config file.")
            config_path = pathlib.Path(f"source/{args.config}")
        else:
            config_path = pathlib.Path(args.config)
        etb.init_testnet(config_path)
        logger.debug("testnet_bootstrapper has finished init-ing the testnet.")

    if args.bootstrap_testnet:
        # the config path lies in /source/data/etb-config.yaml
        config_path = pathlib.Path("source/data/etb-config.yaml")
        etb.bootstrap_testnet(config_path)
        logger.debug("testnet_bootstrapper has finished bootstrapping the testnet.")
