# """
#     Provides a method of gettting a high level overview of the running
#     experiment to check on the health of the network.
#
#     Status checking is done in 3 phases.
#
#     Phase0:
#         allow the network to come up, confirm that things are behaving properly.
#
#     Phase1:
#     	experiment time -- chaos happens and disrupts to network, expect failing
#     	test cases.
#
#     Phase2:
#         runs post-experiment and is a recovery period -- there may be some failing
#         test cases here.
#
#     Phase3:
#         post-recovery verification -- there should not be any failing test cases
#         here.
# """
from modules.ETBConfig import ETBConfig
from modules.BeaconAPI import ETBConsensusBeaconAPI, APIRequest
import json


def check_heads(etb_beacon_api):
    api_request = APIRequest("/eth/v2/beacon/blocks/head")
    all_responses = {}
    for name, response in etb_beacon_api.do_api_request(
        api_request, all_clients=True
    ).items():
        slot = response.json()["data"]["message"]["slot"]
        state_root = response.json()["data"]["message"]["state_root"]
        all_responses[name] = (slot, state_root)

    unique_responses = {}

    for name, response in all_responses.items():
        if response in unique_responses:
            unique_responses[response].append(name)
        else:
            unique_responses[response] = [name]

    return unique_responses


def wait_for_time(milestone, t, etb_beacon_api=None, do_check_heads=False):
    while int(time.time()) < t:
        time_left = t - int(time.time())
        print(
            f"status-check: waiting for {milestone}.. {time_left} seconds remain",
            flush=True,
        )
        if time_left > 15:
            if do_check_heads:
                unique_heads = check_heads(etb_beacon_api)
                print(f"{unique_heads}", flush=True)
            time.sleep(15)
        else:
            time.sleep(1)


def do_phase_analysis(log_prefix, etb_beacon_api):
    for x in range(args.num_checks):
        unique_heads = check_heads(etb_beacon_api)
        if len(unique_heads) == 1:
            print(f"{log_prefix}: Consensus")
            print(f"{unique_heads}", flush=True)
        else:
            print(f"{log_prefix}: Fork Detected")
            print(f"{unique_heads}", flush=True)

        time.sleep(args.check_delay)


def watch_experiment_for_forks(args):
    etb_config = ETBConfig(args.config)
    etb_beacon_api = ETBConsensusBeaconAPI(etb_config, 3, retries=2)

    now = int(time.time())

    if etb_config.get("preset-base") == "mainnet":
        seconds_per_eth2_block = 12
    else:
        raise Exception("No minimal support")

    genesis_time = now + etb_config.get("consensus-genesis-delay")
    phase0_time = now + args.phase0_slot * seconds_per_eth2_block
    phase1_time = now + args.phase1_slot * seconds_per_eth2_block
    phase2_time = now + args.phase2_slot * seconds_per_eth2_block

    # go ahead and get past genesis
    wait_for_time("genesis", genesis_time)
    wait_for_time(
        "phase0", phase0_time, etb_beacon_api=etb_beacon_api, do_check_heads=True
    )
    do_phase_analysis("phase0", etb_beacon_api)
    wait_for_time(
        "phase1", phase1_time, etb_beacon_api=etb_beacon_api, do_check_heads=True
    )
    do_phase_analysis("phase1", etb_beacon_api)
    wait_for_time(
        "phase2", phase2_time, etb_beacon_api=etb_beacon_api, do_check_heads=True
    )
    do_phase_analysis("phase2", etb_beacon_api)


if __name__ == "__main__":
    import argparse
    import time

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
        default=2,
        help="when doing multiple checks how long to pause between them",
    )
    args = parser.parse_args()

    if args.phase0_slot > args.phase1_slot or args.phase0_slot > args.experiment_slot:
        print("WARN: phase0 and phase1/experiment slots are in wrong order", flush=True)
        print("WARN: continuing anyway...")

    if args.phase1_slot > args.phase2_slot or args.phase1_slot > args.experiment_slot:
        print("WARN: phase1 and phase2/experiment slots are in wrong order", flush=True)
        print("WARN: continuing anyway...")

    watch_experiment_for_forks(args)
    print("workload_complete", flush=True)
