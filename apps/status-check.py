"""
    Provides a method of gettting a high level overview of the running
    experiment to check on the health of the network.

    Status checking is done in 3 phases.

    Phase0:
        allow the network to come up, confirm that things are behaving properly.
        if there has been an issue print termination message.

    Phase1:
    	  Phase 1 starts is the starting point for experimentation/chaos.

    Phase2:
        This is the endpoint for chaos. There may be some issues but we wait
        until phase3 for to test for failures.

    Phase3:
        Phase3 marks the point where the network should of healed. All issues
        at this point should be considered errors.
"""
import time
from pathlib import Path

from modules.BeaconAPI import BeaconAPI, ETBConsensusBeaconAPI
from modules.ETBConfig import ETBConfig
from modules.TestnetHealthMetrics import UniqueConsensusHeads


class TestnetStatusChecker(object):
    """
    Status Checker checks the network at important intervals and outputs
    the current heads of the clients approx. every slot

    0. consensus genesis time. This is when we start monitoring.
    1. phase0, we make sure that all the clients in the experiment came up
        if not then we signal to terminate.
    2. phase1, we start the experiment
    3. phase2, we end the experiment
    4. phase3, we check to see if the network healed.
    """

    def __init__(self, args):
        self.etb_config = ETBConfig(args.config)
        self.now = self.etb_config.get("bootstrap-genesis")
        self.consensus_genesis_delay = self.etb_config.get_consensus_genesis_delay()
        self.no_terminate = args.no_terminate
        self.etb_beacon_api = ETBConsensusBeaconAPI(
            self.etb_config,
            non_error=True,
            timeout=args.beaconapi_timeout,
            retry_delay=1,
        )
        self.health_metric = UniqueConsensusHeads()

        self.secs_per_eth2_slot = 12

        self.genesis_time = self.etb_config.get("bootstrap-genesis") + self.consensus_genesis_delay

        self.phase0_time = (
            self.genesis_time + args.phase0_slot * self.secs_per_eth2_slot
        )
        self.phase1_time = (
            self.genesis_time + args.phase1_slot * self.secs_per_eth2_slot
        )
        self.phase2_time = (
            self.genesis_time + args.phase2_slot * self.secs_per_eth2_slot
        )
        self.phase3_time = (
            self.genesis_time + args.phase3_slot * self.secs_per_eth2_slot
        )
        # number of checks just in case we fall on a boundry.
        self.number_of_checks = args.num_checks
        self.check_delay = args.check_delay

        # formatting for output
        self.log_prefix = args.log_prefix
        # if a status check passes
        self.pass_prefix = args.pass_prefix
        # if a status check fails
        self.fail_prefix = args.fail_prefix
        # signal an early termination.
        self.terminate_experiment_string = args.terminate_experiment_string

    def update_health_metric(self):
        curr_check = 0
        while curr_check < self.number_of_checks:
            unique_heads = self.health_metric.perform_metric(self.etb_beacon_api)
            if len(unique_heads.keys()) == 1:
                return unique_heads
            curr_check += 1
            time.sleep(self.check_delay)
        return unique_heads

    def testnet_healthy(self):
        curr_check = 0

        unique_heads = self.update_health_metric()
        if len(unique_heads.keys()) == 1:
            print(f"{self.pass_prefix} : {self.health_metric}", flush=True)
            return True
        print(f"{self.fail_prefix} : {self.health_metric}", flush=True)
        return False

    def start_experiment(self):
        print(f"{self.log_prefix}: start_faults", flush=True)
        # import experiment modules here

    def stop_experiment(self):
        print(f"{self.log_prefix}: stop_faults", flush=True)

    def wait_until(self, log_prefix, t, do_check_heads=False):
        """
        Wait in units of secs_per_slot, unless the time left is less than
        that.

        Optionally print out the health metric inbetween waits.
        """
        while int(time.time()) < t:
            now = int(time.time())
            time_left = t - now
            print(
                f"status-check: {log_prefix}.. {time_left} seconds remain",
                flush=True,
            )
            if time_left > self.secs_per_eth2_slot:
                wait_time = self.secs_per_eth2_slot
                if do_check_heads:
                    self.update_health_metric()
                    print(self.health_metric.__repr__(), flush=True)
                    # accommodate the time it took to run metric.
                    skew = int(time.time()) - now
                    skew_wait = self.secs_per_eth2_slot - skew
                    if skew_wait > 0:
                        time.sleep(skew_wait)
                else:
                    time.sleep(wait_time)

            else:
                time.sleep(1)

    def start_indefinite_checker(self):
        while True:
            self.update_health_metric()
            print(self.health_metric.__repr__(), flush=True)
            time.sleep(self.secs_per_eth2_slot)

    def start_status_checker(self):
        print(f"starting the status checker, delaying {int(time.time()) - self.genesis_time} seconds for consensus genesis.")
        self.wait_until("genesis", int(self.genesis_time))
        print(f"{self.log_prefix}: Consensus Genesis Occurred", flush=True)

        if self.no_terminate:
            print("Running checker in indefinite mode.")
            self.start_indefinite_checker()
        # wait until phase0 to ensure all is working.
        self.wait_until("phase0", self.phase0_time, do_check_heads=True)
        if self.testnet_healthy():
            print(f"{self.log_prefix}: Phase0 passed.", flush=True)
            print(f"{self.health_metric.__repr__()}", flush=True)
        else:
            print(f"{self.log_prefix}: Phase0 failed.", flush=True)
            print(f"{self.health_metric.__repr__()}", flush=True)
            print(f"{self.log_prefix}: terminate")

        self.wait_until("phase1", self.phase1_time, do_check_heads=True)
        self.start_experiment()

        self.wait_until("phase2", self.phase2_time, do_check_heads=True)
        self.stop_experiment()
        print(f"{self.log_prefix}: Phase2 elapsed", flush=True)

        self.wait_until("phase3", self.phase3_time, do_check_heads=True)
        if self.testnet_healthy():
            print(f"{self.log_prefix}: Phase3 passed.", flush=True)
        else:
            print(f"{self.log_prefix}: Phase3 failed.", flush=True)


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
        "--no-terminate",
        dest="no_terminate",
        required=False,
        default=False,
        action="store_true",
        help="run the status checker forever.",
    )
    parser.add_argument(
        "--phase0-slot",
        dest="phase0_slot",
        default=32,
        type=int,
        help="number of slots to wait before checking initial network health.",
    )
    parser.add_argument(
        "--phase1-slot",
        dest="phase1_slot",
        default=128,
        type=int,
        help="number of slots to wait until we introduce experiment.",
    )
    parser.add_argument(
        "--phase2-slot",
        dest="phase2_slot",
        type=int,
        default=160,
        help="number of slots to wait until we end experiment.",
    )

    parser.add_argument(
        "--phase3-slot",
        dest="phase3_slot",
        type=int,
        default=164,
        help="number of slots to wait for the network to heal itself.",
    )

    parser.add_argument(
        "--number-of-checks",
        dest="num_checks",
        default=3,
        type=int,
        help="how many loops to run the health check per run.",
    )

    parser.add_argument(
        "--check-delay",
        dest="check_delay",
        default=2,
        type=int,
        help="how long to wait between loops for health check re-check.",
    )

    parser.add_argument(
        "--beaconapi-timeout",
        dest="beaconapi_timeout",
        default=2,
        type=int,
        help="How long for the BeaconAPI obj to consider a query timeout",
    )

    parser.add_argument(
        "--log-prefix",
        dest="log_prefix",
        default="etb-testnet",
        help="prefix for logging.",
    )

    parser.add_argument(
        "--pass-prefix",
        dest="pass_prefix",
        default="SUCCESS",
        help="log string for when we pass a health check/phase check.",
    )

    parser.add_argument(
        "--fail-prefix",
        dest="fail_prefix",
        default="FAIL",
        help="log string for when we fail a health check/phase check.",
    )

    parser.add_argument(
        "--terminate-experiment-prefix",
        dest="terminate_experiment_string",
        default="terminate",
        help="string to print if we fail phase0.",
    )

    args = parser.parse_args()

    while not Path("/data/etb-config-file-ready").exists():
        time.sleep(1)

    status_checker = TestnetStatusChecker(args)
    status_checker.start_status_checker()

    print(f"{status_checker.log_prefix}: workload_complete", flush=True)
