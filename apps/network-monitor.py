"""
    Useful for monitoring the status of the network to find issues.
"""

from modules.ETBConfig import ETBConfig
from modules.TestnetHealthMetrics import TestnetHealthAPI, GetUniqueHeads
import argparse
import time

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        dest="config",
        required=True,
        help="path to config file to consume for experiment",
    )

    parser.add_argument(
        "--consensus-heads",
        dest="consensus_heads",
        action="store_true",
        default=True,
        help="log consensus client head slot and state_root",
    )

    parser.add_argument(
        "--update-delay",
        dest="update_delay",
        type=int,
        default=12,
        help="how often we query the network.",
    )

    args = parser.parse_args()
    time.sleep(30) #TODO: use a checkpoint file.
    etb_config = ETBConfig(args.config)
    now = etb_config.get("bootstrap-genesis")
    monitor = TestnetHealthAPI(etb_config)

    if args.consensus_heads:
        monitor.add_metric(GetUniqueHeads(), "consensus-heads")

    genesis = now + etb_config.get("consensus-genesis-delay")

    curr_time = int(time.time())
    while curr_time < genesis:
        ttg = genesis - curr_time

        if ttg > 30:
            time.sleep(30)

        else:
            time.sleep(5)

        print(f"waiting for genesis {ttg} seconds remain..", flush=True)
        curr_time = int(time.time())

    while True:
        monitor.perform_all_metrics()
        print(monitor.__repr__(), flush=True)
        time.sleep(args.update_delay)
