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
import logging
import time
from pathlib import Path

from modules.TestnetMonitor import (
    TestnetMonitor,
    TestnetMonitorAction,
    ActionInterval,
    ActionIntervalType,
)
from modules.ClientRequest import perform_batched_request, beacon_getBlockV2

# from modules.BeaconAPI import BeaconAPI, ETBConsensusBeaconAPI
from modules.ETBConfig import ETBConfig, ClientInstance

# from modules.TestnetHealthMetrics import UniqueConsensusHeads


# class TestnetStatusChecker(object):
#     """
#     Status Checker checks the network at important intervals and outputs
#     the current heads of the clients approx. every slot
#
#     0. consensus genesis time. This is when we start monitoring.
#     1. phase0, we make sure that all the clients in the experiment came up
#         if not then we signal to terminate.
#     2. phase1, we start the experiment
#     3. phase2, we end the experiment
#     4. phase3, we check to see if the network healed.
#     """
#
#     def __init__(self, args):
#         self.etb_config = ETBConfig(args.config)
#         self.now = self.etb_config.get("bootstrap-genesis")
#         self.consensus_genesis_delay = self.etb_config.get_consensus_genesis_delay()
#         self.no_terminate = args.no_terminate
#         self.etb_beacon_api = ETBConsensusBeaconAPI(
#             self.etb_config,
#             non_error=True,
#             timeout=args.beaconapi_timeout,
#             retry_delay=1,
#         )
#
#         self.health_metric = UniqueConsensusHeads()
#
#         self.secs_per_eth2_slot = self.etb_config.preset_base.SECONDS_PER_SLOT.value
#
#         self.genesis_time = self.etb_config.get("bootstrap-genesis") + self.consensus_genesis_delay
#
#         self.phase0_time = (
#             self.genesis_time + args.phase0_slot * self.secs_per_eth2_slot
#         )
#         self.phase1_time = (
#             self.genesis_time + args.phase1_slot * self.secs_per_eth2_slot
#         )
#         self.phase2_time = (
#             self.genesis_time + args.phase2_slot * self.secs_per_eth2_slot
#         )
#         self.phase3_time = (
#             self.genesis_time + args.phase3_slot * self.secs_per_eth2_slot
#         )
#         # number of checks just in case we fall on a boundry.
#         self.number_of_checks = args.num_checks
#         self.check_delay = args.check_delay
#
#         # formatting for output
#         self.log_prefix = args.log_prefix
#         # if a status check passes
#         self.pass_prefix = args.pass_prefix
#         # if a status check fails
#         self.fail_prefix = args.fail_prefix
#         # signal an early termination.
#         self.terminate_experiment_string = args.terminate_experiment_string
#
#     def update_health_metric(self):
#         curr_check = 0
#         while curr_check < self.number_of_checks:
#             unique_heads = self.health_metric.perform_metric(self.etb_beacon_api)
#             if len(unique_heads.keys()) == 1:
#                 return unique_heads
#             curr_check += 1
#             time.sleep(self.check_delay)
#         return unique_heads
#
#     def testnet_healthy(self):
#         curr_check = 0
#
#         unique_heads = self.update_health_metric()
#         if len(unique_heads.keys()) == 1:
#             print(f"{self.pass_prefix} : {self.health_metric}", flush=True)
#             return True
#         print(f"{self.fail_prefix} : {self.health_metric}", flush=True)
#         return False
#
#     def start_experiment(self):
#         print(f"{self.log_prefix}: start_faults", flush=True)
#         # import experiment modules here
#
#     def stop_experiment(self):
#         print(f"{self.log_prefix}: stop_faults", flush=True)
#
#     def wait_until(self, log_prefix, t, do_check_heads=False):
#         """
#         Wait in units of secs_per_slot, unless the time left is less than
#         that.
#
#         Optionally print out the health metric inbetween waits.
#         """
#         while int(time.time()) < t:
#             now = int(time.time())
#             time_left = t - now
#             print(
#                 f"status-check: {log_prefix}.. {time_left} seconds remain",
#                 flush=True,
#             )
#             if time_left > self.secs_per_eth2_slot:
#                 wait_time = self.secs_per_eth2_slot
#                 if do_check_heads:
#                     self.update_health_metric()
#                     print(self.health_metric.__repr__(), flush=True)
#                     # accommodate the time it took to run metric.
#                     skew = int(time.time()) - now
#                     skew_wait = self.secs_per_eth2_slot - skew
#                     if skew_wait > 0:
#                         time.sleep(skew_wait)
#                 else:
#                     time.sleep(wait_time)
#
#             else:
#                 time.sleep(1)
#
#     def start_indefinite_checker(self):
#         while True:
#             self.update_health_metric()
#             print(self.health_metric.__repr__(), flush=True)
#             time.sleep(self.secs_per_eth2_slot)
#
#     def start_status_checker(self):
#         print(f"starting the status checker, delaying {int(time.time()) - self.genesis_time} seconds for consensus genesis.")
#         self.wait_until("genesis", int(self.genesis_time))
#         print(f"{self.log_prefix}: Consensus Genesis Occurred", flush=True)
#
#         if self.no_terminate:
#             print("Running checker in indefinite mode.")
#             self.start_indefinite_checker()
#         # wait until phase0 to ensure all is working.
#         self.wait_until("phase0", self.phase0_time, do_check_heads=True)
#         if self.testnet_healthy():
#             print(f"{self.log_prefix}: Phase0 passed.", flush=True)
#             print(f"{self.health_metric.__repr__()}", flush=True)
#         else:
#             print(f"{self.log_prefix}: Phase0 failed.", flush=True)
#             print(f"{self.health_metric.__repr__()}", flush=True)
#             print(f"{self.log_prefix}: terminate")
#
#         self.wait_until("phase1", self.phase1_time, do_check_heads=True)
#         self.start_experiment()
#
#         self.wait_until("phase2", self.phase2_time, do_check_heads=True)
#         self.stop_experiment()
#         print(f"{self.log_prefix}: Phase2 elapsed", flush=True)
#
#         self.wait_until("phase3", self.phase3_time, do_check_heads=True)
#         if self.testnet_healthy():
#             print(f"{self.log_prefix}: Phase3 passed.", flush=True)
#         else:
#             print(f"{self.log_prefix}: Phase3 failed.", flush=True)

"""
        unique_resps = {}
        for name, response in all_responses.items():
            if response in unique_resps:
                unique_resps[response].append(name)
            else:
                unique_resps[response] = [name]

        num_heads = len(unique_resps.keys())

        if num_heads != 1:
            self.result = f"found {num_heads-1} forks: {unique_resps}"
        else:
            slot, state_root, graffiti = list(unique_resps.keys())[0]
            self.result = f"found {num_heads-1} forks: {slot}:{state_root}:{graffiti}"
"""

"""
    get_heads_status_check_slot is used for indefinite testnets to continuously
    print out the current state of the network heads. Its fast but less
    accurate. 
    
    returns a string to be printed out by the testnet monitor.
"""


def get_heads_status_check_slot(clients_to_monitor: list[ClientInstance]) -> str:
    """
    Returns the strings to print per slot and a boolean if there is a fork. Note
    this isn't accurate because one client could be behind or we could be
    slightly skewed.
    :param clients_to_monitor:
    :param clients:
    :return: health_network (bool) : out str
    """
    unreachable_clients = []
    unique_responses: dict[str, list[str]] = {}

    state_root_to_blk: dict[str, dict] = {}

    rpc_request = beacon_getBlockV2()
    for client, result in perform_batched_request(rpc_request, clients_to_monitor):
        error, response = result
        if error is None:
            block = rpc_request.retrieve_response(response)
            slot = block["slot"]
            state_root = str(block["state_root"])
            graffiti = (
                bytes.fromhex(block["body"]["graffiti"][2:])
                .decode("utf-8")
                .replace("\x00", "")
            )
            blk_report = {
                "slot": slot,
                "state-root": state_root,
                "graffiti": graffiti,
            }
            if state_root not in unique_responses:
                unique_responses[state_root] = [client.name]
                state_root_to_blk[state_root] = blk_report
            else:
                unique_responses[state_root].append(client.name)

        else:
            unreachable_clients.append(client.name)

    num_forks = len(unique_responses.keys()) - 1
    if len(unreachable_clients) > 0:
        num_forks += 1

    out = f"found {num_forks} forks: "
    for state_root in unique_responses.keys():
        blk_report = state_root_to_blk[state_root]
        out += (
            f"{blk_report['slot']}:{blk_report['state-root']}:{blk_report['graffiti']}"
        )
        out += f"  {unique_responses[state_root]}\n"
    if len(unreachable_clients) > 0:
        out += f"unreachable hosts: {unreachable_clients}\n"
    return out


"""
    Tries running the same logic as get_heads_status_check_slot but retries
    if we fail to come to consensus.
"""


def check_for_consensus(
    clients_to_monitor: list[ClientInstance], max_retries=3
) -> bool:
    """
        This is the same as the per slot check except we will try multiple times
        to try and find consensus.
    :param clients_to_monitor:
    :return:
    """
    unreachable_clients = []
    unique_responses: dict[str, list[str]] = {}
    state_root_to_blk: dict[str, dict] = {}

    found_consensus = False
    curr_try = 0
    while not found_consensus or curr_try > max_retries:
        curr_try += 1
        unreachable_clients = []
        unique_responses: dict[str, list[str]] = {}
        state_root_to_blk: dict[str, dict] = {}
        rpc_request = beacon_getBlockV2()
        for client, result in perform_batched_request(rpc_request, clients_to_monitor):
            error, response = result
            if error is None:
                block = rpc_request.retrieve_response(response)
                slot = block["slot"]
                state_root = str(block["state_root"])
                graffiti = (
                    bytes.fromhex(block["body"]["graffiti"][2:])
                    .decode("utf-8")
                    .replace("\x00", "")
                )
                blk_report = {
                    "slot": slot,
                    "state-root": state_root,
                    "graffiti": graffiti,
                }
                if state_root not in unique_responses:
                    unique_responses[state_root] = [client.name]
                    state_root_to_blk[state_root] = blk_report
                else:
                    unique_responses[state_root].append(client.name)

            else:
                unreachable_clients.append(client.name)
        if len(unreachable_clients) == 0 and len(list(unique_responses.keys())) == 1:
            found_consensus = True

    num_forks = len(unique_responses.keys()) - 1
    if len(unreachable_clients) > 0:
        num_forks += 1

    out = f"found {num_forks} forks: "
    for state_root in unique_responses.keys():
        blk_report = state_root_to_blk[state_root]
        out += (
            f"{blk_report['slot']}:{blk_report['state-root']}:{blk_report['graffiti']}"
        )
        out += f"  {unique_responses[state_root]}\n"
    if len(unreachable_clients) > 0:
        out += f"unreachable hosts: {unreachable_clients}\n"

    print(out, flush=True)
    return found_consensus


class StatusCheckPerSlotHeadMonitor(TestnetMonitorAction):
    def __init__(self, clients_to_check: list[ClientInstance]):
        super().__init__(
            ActionInterval(1, ActionIntervalType.ON_SLOT),
            get_heads_status_check_slot,
            [clients_to_check],
        )


class TestnetStatusCheckerV2(object):
    def __init__(self, etb_config: ETBConfig, logger: logging.Logger = None):
        self.etb_config: ETBConfig = etb_config

        if logger is None:
            self.logger = logging.getLogger("testnet-status-checker")
        else:
            self.logger = logger

        self.clients_to_monitor = self.etb_config.get_client_instances()
        self.testnet_monitor = TestnetMonitor(self.etb_config)

    def perform_finite_status_check(self, args):
        # go ahead and get the defaults.
        slots_per_epoch = self.etb_config.preset_base.SLOTS_PER_EPOCH.value
        if args.phase0_slot == -1:
            phase0_slot = slots_per_epoch
        else:
            phase0_slot = args.phase0_slot

        if args.phase1_slot == -1:
            phase1_slot = 2 * slots_per_epoch
        else:
            phase1_slot = args.phase1_slot

        if args.phase2_slot == -1:
            phase2_slot = 3 * slots_per_epoch
        else:
            phase2_slot = args.phase2_slot

        if args.phase3_slot == -1:
            phase3_slot = 4 * slots_per_epoch
        else:
            phase3_slot = args.phase3_slot
        print(f"phase0_slot: {phase0_slot}\nphase1_slot: {phase1_slot}\n", flush=True)
        print(f"phase2_slot: {phase2_slot}\nphase3_slot: {phase3_slot}\n", flush=True)

        self.testnet_monitor.wait_for_slot(phase0_slot)
        if check_for_consensus(self.clients_to_monitor):
            print(f"Phase0 passed.", flush=True)
        else:
            print(f"Phase0 failed.", flush=True)
            print(f": terminate")

        self.testnet_monitor.wait_for_slot(phase1_slot)
        print(f"start_faults", flush=True)

        while self.testnet_monitor.get_slot() < phase2_slot:
            self.testnet_monitor.wait_for_next_slot()
            print(get_heads_status_check_slot(self.clients_to_monitor), flush=True)

        print(f"stop_faults", flush=True)
        print(f"Phase2 elapsed", flush=True)
        while self.testnet_monitor.get_slot() < phase3_slot:
            self.testnet_monitor.wait_for_next_slot()
            print(get_heads_status_check_slot(self.clients_to_monitor), flush=True)

        if check_for_consensus(self.clients_to_monitor):
            print(f"Phase3 passed.", flush=True)
        else:
            print(f"Phase3 failed.", flush=True)

        print(f"workload_complete", flush=True)

    def perform_indefinite_status_check(self):
        self.logger.debug(
            f"Indefinite status check: clients to monitor: {self.clients_to_monitor}"
        )
        per_slot_action = StatusCheckPerSlotHeadMonitor(self.clients_to_monitor)
        self.testnet_monitor.add_action(per_slot_action)
        self.testnet_monitor.start()


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
        help="Just run the testnet and check the heads every slot. (defaults to true)",
    )

    parser.add_argument(
        "--phase0-slot",
        dest="phase0_slot",
        default=-1,
        type=int,
        help="number of slots to wait before checking initial network health. (defaults to 1st epoch)",
    )

    parser.add_argument(
        "--phase1-slot",
        dest="phase1_slot",
        default=-1,
        type=int,
        help="number of slots to wait until we introduce experiment. (defaults to 2nd epoch)",
    )
    parser.add_argument(
        "--phase2-slot",
        dest="phase2_slot",
        type=int,
        default=-1,
        help="number of slots to wait until we end experiment. (defaults to 3rd epoch)",
    )

    parser.add_argument(
        "--phase3-slot",
        dest="phase3_slot",
        type=int,
        default=-1,
        help="number of slots to wait for the network to heal itself. (defaults to 4th epoch)",
    )

    args = parser.parse_args()

    while not Path("/data/etb-config-file-ready").exists():
        time.sleep(1)

    logger = logging.getLogger()

    status_checker = TestnetStatusCheckerV2(ETBConfig(args.config, logger), logger)

    if args.no_terminate:
        logger.info("Performing continuous status check.")
        status_checker.perform_indefinite_status_check()
    else:
        logger.info("Performing antithesis experiment.")
        status_checker.perform_finite_status_check(args)
