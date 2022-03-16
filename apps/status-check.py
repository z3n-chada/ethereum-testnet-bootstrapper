"""
    Provides a method of gettting a high level overview of the running
    experiment to check on the health of the network.

    Status checking is done in 3 phases.

    Phase0:
        allow the network to come up, confirm that things are behaving properly.

    Phase1:
    	experiment time -- chaos happens and disrupts to network, expect failing
    	test cases.
    	
    Phase2:
        runs post-experiment and is a recovery period -- there may be some failing
        test cases here.

    Phase3:
        post-recovery verification -- there should not be any failing test cases 
        here.
"""
import time
from modules.BeaconApi import APIRequest, get_api_manager_from_config
import concurrent.futures

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
    print("Launching Experiment!")
    # import experiment modules here.


def check_health(manager, num_checks, check_delay, log_prefix):
    for i in range(num_checks):
        for qp in health_check_apis["queryPaths"]:
            vals = []
            for client in manager.clients.values():
                vals.append(str(qp.get_response(client)))
            if len(list(set(vals))) > 1:
                print(f"{log_prefix}: Error, query={qp}")
            else:
                print(f"{log_prefix}: Consensus, query={qp}")

        for sp in statePaths:
            for s in states:
                r = APIRequest(f"/eth/v1/beacon/states/{s}/{sp}")
                vals = []
                for client in manager.clients.values():
                    vals.append(str(r.get_response(client)))
                if len(list(set(vals))) > 1:
                    print(f"{log_prefix}: Error, query={r}")
                else:
                    print(f"{log_prefix}: Consensus, query={r}")

        time.sleep(check_delay)


def wait_for_slot(manager, goal_slot):
    node_count = len(manager.clients)
    curr_slots = [0 for _ in manager.clients.keys()]
    with concurrent.futures.ThreadPoolExecutor() as e:
        while len([s for s in curr_slots if s >= goal_slot]) < node_count:
            tasks = [e.submit(c.get_head_block_header) for c in manager.clients.values()]
            # get_head_block_header() has a built-in retry to protect against node failures. If
            # all retries have been exhausted, the response has data set to None.
            # If the response data is None, we don't want the loop to continue indefinitely so 
            # return the goal slot.
            resps = [t.result() for t in tasks]
            curr_slots = [int(r.data["header"]["message"]["slot"]) if r.data else goal_slot for r in resps]
            print(curr_slots, flush=True)
            time.sleep(5)


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
        "--experiment-slot",
        dest="experiment_slot",
        default=64,
        type=int,
        help="number of slots to wait before checking initial network health",
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

    parser.add_argument(
        "--number-of-checks",
        dest="num_checks",
        default=3,
        type=int,
        help="how many loops to run the health check per run",
    )

    parser.add_argument(
        "--check-delay",
        dest="check_delay",
        type=int,
        default=10,
        help="when doing multiple checks how long to pause between them",
    )
    args = parser.parse_args()

    if args.phase0_slot > args.phase1_slot or args.phase0_slot > args.experiment_slot:
        print("WARN: phase0 and phase1/experiment slots are in wrong order", flush=True)
        print("WARN: continuing anyway...")

    if args.phase1_slot > args.phase2_slot or args.phase1_slot > args.experiment_slot:
        print("WARN: phase1 and phase2/experiment slots are in wrong order", flush=True)
        print("WARN: continuing anyway...")

    manager = get_api_manager_from_config(args.config)

    # wait for network init.
    time.sleep(args.genesis_delay)
    # phase0
    wait_for_slot(manager, args.phase0_slot)
    
    # phase1
    perform_experiment()
    check_health(manager, args.num_checks, args.check_delay, "phase1")
    wait_for_slot(manager, args.phase1_slot)
    
    # phase2
    check_health(manager, args.num_checks, args.check_delay, "phase2")
    wait_for_slot(manager, args.phase2_slot)
    
    # phase3
    check_health(manager, args.num_checks, args.check_delay, "phase3")
    
    print("workload_complete", flush=True)
