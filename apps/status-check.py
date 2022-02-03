"""
    Provides a method of gettting a high level overview of the running experiment
    to check on the health of the network.
"""
from modules.BeaconApi import get_api_manager_from_config
import time

# api_requests to run to comapre nodes.
health_check_apis = {}


def perform_experiment():
    print("TODO")


def check_health(manager):
    for metric, api in health_check_apis.values():
        print("TODO")


def wait_for_slot(manager, goal_slot):
    goal = [goal_slot for x in range(len(manager.clients.keys()))]
    curr_slots = []
    # should be more robust.
    while curr_slots != goal:
        curr_slots = []
        for c in manager.clients:
            slot = (
                manager.clients[c]
                .get_head_block_header()
                .data["header"]["message"]["slot"]
            )
            curr_slots.append(int(slot))
        time.sleep(1)
        print(curr_slots, flush=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        dest="config",
        required=True,
        help="path to config file to consume for experiment",
    )
    parser.add_argument(
        "--phase0-slot",
        dest="phase0_slot",
        default=64,
        type=int,
        help="number of slots to wait before checking initial network health",
    )
    parser.add_argument(
        "--phase1-slot",
        dest="phase1_slot",
        default=96,
        type=int,
        help="number of slots to wait to check for post-scenario network health",
    )
    parser.add_argument(
        "--phase2-slot",
        dest="phase2_slot",
        type=int,
        default=160,
        help="slot to wait to check for network recovery",
    )
    args = parser.parse_args()

    manager = get_api_manager_from_config(args.config)

    # wait for network init.
    wait_for_slot(manager, args.phase0_slot)
    check_health(manager)
    perform_experiment()
    wait_for_slot(manager, args.phase1_slot)
    check_health(manager)
    wait_for_slot(manager, args.phase2_slot)
    check_health(manager)
