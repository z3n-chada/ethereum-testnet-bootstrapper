"""
    Provides a method of gettting a high level overview of the running experiment
    to check on the health of the network.
"""
from modules.BeaconApi import get_api_manager_from_config, APIRequest
import time

# api_requests to run to comapre nodes.
health_check_apis = {
    "queryPaths": [
        APIRequest("/eth/v1/beacon/headers"),
        APIRequest("/eth/v1/beacon/pool/attestations"),
        APIRequest("/eth/v1/beacon/pool/attester_slashings"),
        APIRequest("/eth/v1/beacon/pool/proposer_slashings"),
        APIRequest("/eth/v1/beacon/pool/voluntary_exits"),
        APIRequest("/eth/v1/debug/beacon/heads"),
        APIRequest("/eth/v1/node/syncing"),
    ],
    "headQueryPaths": [APIRequest("/eth/v1/beacon/states/")],
    "slotQueryPaths": [APIRequest("/eth/v1/beacon/blocks/")],
}

statePaths = [
    "committees",
    "validator_balances",
    "root",
    "fork",
    "finality_checkpoints",
]

states = ["head", "justified", "finalized"]


def perform_experiment():
    print("Implement me.")


def check_health(manager):
    for qp in health_check_apis["queryPaths"]:
        vals = []
        for client in manager.clients.values():
            vals.append(str(qp.get_response(client)))
        if len(list(set(vals))) > 1:
            print("Error")
        else:
            print("Consensus")

    for sp in statePaths:
        for s in states:
            r = APIRequest(f"/eth/v1/beacon/states/{s}/{sp}")
            vals = []
            for client in manager.clients.values():
                vals.append(str(r.get_response(client)))
            if len(list(set(vals))) > 1:
                print("Error")
            else:
                print("Consensus")


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
    parser.add_argument(
        "--genesis-delay",
        dest="genesis_delay",
        type=int,
        default=240,
        help="genesis delay to wait for first slot",
    )
    args = parser.parse_args()

    manager = get_api_manager_from_config(args.config)

    # wait for network init.
    time.sleep(args.genesis_delay)
    wait_for_slot(manager, args.phase0_slot)
    check_health(manager)
    perform_experiment()
    wait_for_slot(manager, args.phase1_slot)
    check_health(manager)
    wait_for_slot(manager, args.phase2_slot)
    check_health(manager)
