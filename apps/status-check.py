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
from modules.TestnetHealthMetrics import TestnetHealthAPI, GetUniqueHeads


class TestnetStatusChecker(object):
    def __init__(self, args):
        self.etb_config = ETBConfig(args.config)

        self.thapi = TestnetHealthAPI(self.etb_config)
        self.thapi.add_metric(GetUniqueHeads(), name="consensus-check")

        self.now = int(time.time())

        if self.etb_config.get("preset-base") == "mainnet":
            seconds_per_eth2_slot = 12
        else:
            raise Exception("No minimal support")

        self.genesis_time = self.now + self.etb_config.get("consensus-genesis-delay")
        self.phase0_time = self.now + args.phase0_slot * seconds_per_eth2_slot
        self.exp_time = self.now + args.experiment_slot * seconds_per_eth2_slot
        self.phase1_time = self.now + args.phase1_slot * seconds_per_eth2_slot
        self.phase2_time = self.now + args.phase2_slot * seconds_per_eth2_slot

        self.check_delay = args.check_delay
        self.number_of_checks = args.num_checks

        if (
            args.phase0_slot > args.phase1_slot
            or args.phase0_slot > args.experiment_slot
        ):
            print(
                "WARN: phase0 and phase1/experiment slots are in wrong order",
                flush=True,
            )
            print("WARN: continuing anyway...")

        if (
            args.phase1_slot > args.phase2_slot
            or args.phase1_slot > args.experiment_slot
        ):
            print(
                "WARN: phase1 and phase2/experiment slots are in wrong order",
                flush=True,
            )
            print("WARN: continuing anyway...")

    def wait_for_time(self, log_prefix, t):
        while int(time.time()) < t:
            time_left = t - int(time.time())
            print(
                f"status-check: {log_prefix}.. {time_left} seconds remain",
                flush=True,
            )
            if time_left > 15:
                time.sleep(15)
            else:
                time.sleep(1)

    def perform_status_check(self, log_prefix):
        query = "/eth/v2/beacon/headers/head"
        client_heads = self.thapi.perform_metric("consensus-check")
        unique_resps = {}

        for name, response in client_heads.items():
            if response in unique_resps:
                unique_resps[response].append(name)
            else:
                unique_resps[response] = [name]

        num_heads = len(unique_resps.keys())
        if num_heads != 1:
            print(f"{log_prefix}: Error, query={query}")
            print(unique_resps, flush=True)
        else:
            print(f"{log_prefix}: Consensus, query={query}", flush=True)

    def perform_experiment(self):
        print("Launching Experiment!", flush=True)
        # import experiment modules here

    def start(self):
        self.wait_for_time("genesis", self.genesis_time)
        for x in range(self.number_of_checks):
            self.perform_status_check("genesis")
            time.sleep(self.check_delay)

        self.wait_for_time("phase0", self.phase0_time)
        for x in range(self.number_of_checks):
            self.perform_status_check("phase0")
            time.sleep(self.check_delay)

        self.wait_for_time("experiment", self.exp_time)
        self.perform_experiment()

        self.wait_for_time("phase1", self.phase1_time)
        for x in range(self.number_of_checks):
            self.perform_status_check("phase1")
            time.sleep(self.check_delay)

        self.wait_for_time("phase2", self.phase0_time)
        for x in range(self.number_of_checks):
            self.perform_status_check("phase2")
            time.sleep(self.check_delay)


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
        help="number of slots to wait after experiment for network health",
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
    status_checker = TestnetStatusChecker(args)
    status_checker.start()

    print("workload_complete", flush=True)
