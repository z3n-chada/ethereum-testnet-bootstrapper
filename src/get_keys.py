"""
    Misc script meant to run seperately from testnets. Used to get key information that may be useful for
    cli args for other scripts.
"""

import argparse
import pathlib
import logging

from etb.config.etb_config import ETBConfig
from etb.common.utils import create_logger, get_premine_keypairs


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Fetch public/private key pairs from a config"
    )

    parser.add_argument(
        "--log-level", dest="log_level", type=str, default="info", help="Logging level"
    )

    parser.add_argument(
        "--config", dest="config", type=str, required=True, help="Path to config file"
    )

    args = parser.parse_args()

    etb_config: ETBConfig = ETBConfig(pathlib.Path(args.config))

    create_logger(
        name="keygen",
        log_level=args.log_level.upper(),
        format_str="%(message)s",
    )
    logging.info("el premine keypairs. (public_key:private_key)")
    # show premine keypairs
    for premine in get_premine_keypairs(etb_config):
        logging.info(f"\t{premine.public_key}:{premine.private_key}")

