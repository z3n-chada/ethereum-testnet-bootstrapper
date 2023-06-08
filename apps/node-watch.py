"""
    A simple TestnetAction that reports the current:
        head slot (number, root, graffiti) graffiti will default to proposer instance
        finality checkpoints: (current_justified, finalized) (epoch, root)

    The output is organized in terms of forks seen. Roots are represented by
    the last 6 characters of the root.
"""
import logging
from typing import Generator, Iterator

from modules.TestnetMonitor import TestnetMonitor, ActionInterval, ActionIntervalType, TestnetMonitorAction
from modules.ETBConfig import ETBConfig, ClientInstance
from modules.ClientRequest import perform_batched_request, beacon_getBlockV2, beacon_getFinalityCheckpoints


class NodeWatchReport(object):
    def __init__(self, client_instance: ClientInstance, block_request: beacon_getBlockV2,
                 checkpoint_request: beacon_getFinalityCheckpoints):
        self.client_instance = client_instance
        block_request = block_request
        checkpoint_request = checkpoint_request

        if block_request.valid_response:
            try:
                response = block_request.retrieve_response()
                self.head_slot = response["slot"]
                self.head_root = f"{response['state_root'][-6:]}"
                self.head_graffiti = bytes.fromhex(response["body"]["graffiti"][2:]).decode("utf-8").replace("\x00", "")
            except Exception as e:
                logging.error(f"Error parsing block response: {e}")
                self.head_slot = "error"
                self.head_root = "error"
                self.head_graffiti = "error"
        else:
            # none as a string for an expected error
            self.head_slot = "None"
            self.head_root = "None"
            self.head_graffiti = "None"

        if checkpoint_request.valid_response:
            try:
                response = checkpoint_request.retrieve_response()
                current_justified = response["current_justified"]
                finalized = response["finalized"]
                self.checkpoints = {
                    "current_justified": (current_justified["epoch"], f"{current_justified['root'][-6:]}"),
                    "finalized": (finalized["epoch"], f"{finalized['root'][-6:]}"),
                }
            except Exception as e:
                logging.error(f"Error parsing checkpoint response: {e}")
                self.checkpoints = {"current_justified": "error", "finalized": "error"}
        else:
            # none as a string for an expected error
            self.checkpoints = {"current_justified": "None", "finalized": "None"}

    def __repr__(self):
        head_str = f"(slot: {self.head_slot}, root: {self.head_root}, graffiti: {self.head_graffiti})"
        current_justified_str = f"justified: ({self.checkpoints['current_justified'][0]}, {self.checkpoints['current_justified'][1]})"
        finalized_str = f"finalized: ({self.checkpoints['finalized'][0]}, {self.checkpoints['finalized'][1]})"

        return f"CurrentHead: {head_str}, Checkpoints: ({current_justified_str} : {finalized_str})"

    def __hash__(self):
        # make this hashable for dict keys
        return hash((str(self.head_slot),
                     str(self.head_root),
                     str(self.head_graffiti),
                     str(self.checkpoints["current_justified"][1]),
                     str(self.checkpoints["finalized"][1])))


def get_node_watch_reports(client_instances: list[ClientInstance]) -> Iterator[dict[ClientInstance, NodeWatchReport]]:
    """
        Given a list of client instances, return a dict of the head and finality checkpoints
        for each instance.
    """
    block_requests: dict[ClientInstance, beacon_getBlockV2] = {}
    checkpoint_requests: dict[ClientInstance, beacon_getFinalityCheckpoints] = {}

    for client_instance, block_request in perform_batched_request(beacon_getBlockV2(), client_instances):
        block_requests[client_instance] = block_request
    for client_instance, checkpoint_request in perform_batched_request(beacon_getFinalityCheckpoints(),
                                                                       client_instances):
        checkpoint_requests[client_instance] = checkpoint_request

    for client_instance in client_instances:
        yield client_instance, NodeWatchReport(client_instance,
                                               block_requests[client_instance],
                                               checkpoint_requests[client_instance])


def get_node_watch_report_str(client_instances: list[ClientInstance]) -> str:
    """
        Given a list of client instances, return a string representing the head and finality checkpoints
        for each instance.
    """
    unique_reports: dict[NodeWatchReport, list[ClientInstance]] = {}
    for instance, report in get_node_watch_reports(client_instances):
        if report.__repr__() not in unique_reports:
            unique_reports[report.__repr__()] = []
        unique_reports[report.__repr__()].append(report.client_instance.name)

    num_forks = len(unique_reports.keys()) - 1
    out = f"Number of forks: {num_forks}\n"
    for report, instances in unique_reports.items():
        out += f"{str(report)}: [{', '.join(map(str, instances))}]\n"
    return out


class NodeWatchAction(TestnetMonitorAction):
    def __init__(self, instances_to_check: list[ClientInstance]):
        super().__init__(ActionInterval(1, ActionIntervalType.ON_SLOT),
                         get_node_watch_report_str,
                         [instances_to_check])  # TODO why is this a list of lists?


class SimpleNodeWatch(object):
    def __init__(self, etb_config: ETBConfig, logger: logging.Logger = None):
        self.etb_config: ETBConfig = etb_config

        if logger is None:
            self.logger = logging.getLogger("testnet-node-watch")

        self.instances_to_monitor = self.etb_config.get_client_instances()
        self.monitor = TestnetMonitor(self.etb_config, logger=logger)
        self.monitor.add_action(NodeWatchAction(self.instances_to_monitor))


if __name__ == "__main__":

    import argparse
    import time
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Testnet Node Watch")

    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")

    args = parser.parse_args()
    while not Path("/data/etb-config-file-ready").exists():
        time.sleep(1)

    node_watcher = SimpleNodeWatch(ETBConfig(args.config))
    node_watcher.monitor.start()
