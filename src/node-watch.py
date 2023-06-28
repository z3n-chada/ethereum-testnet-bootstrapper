"""
    A simple TestnetAction that reports the current:
        head slot (number, root, graffiti) graffiti will default to proposer instance
        finality checkpoints: (current_justified, finalized) (epoch, root)

    The output is organized in terms of forks seen. Roots are represented by
    the last 6 characters of the root.
"""
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
import logging
import time
from typing import Union, Any

import requests

from etb.common.Consensus import ConsensusFork, Epoch
from etb.common.Utils import create_logger, logging_levels
from etb.config.ETBConfig import ETBConfig, ClientInstance, get_etb_config
from etb.interfaces.TestnetMonitor import TestnetMonitor, TestnetMonitorAction, TestnetMonitorActionInterval
from etb.interfaces.ClientRequest import beacon_getBlockV2, perform_batched_request, ClientInstanceRequest, \
    beacon_getFinalityCheckpoints


class NodeWatchResult(object):
    """
    The result of a NodeWatchMetric.
    results: a dictionary of results, where the key is the result and the value is a list of client instances that returned that result.
    unreachable_clients: a list of client instances that were unreachable.
    invalid_response_clients: a list of client instances that returned an invalid response.
    """

    def __init__(self, results: dict[Any, list[ClientInstance]], unreachable_clients: list[ClientInstance],
                 invalid_response_clients: list[ClientInstance]):
        self.results = results
        self.unreachable_clients = unreachable_clients
        self.invalid_response_clients = invalid_response_clients


class NodeWatchMetric(object):
    """
    A metric to be captured across some client instances.
    """

    def __init__(self, request: ClientInstanceRequest, name: str, max_retries_for_consensus: int = 3):
        self.request = request
        self.name = name
        self.max_retries_for_consensus = max_retries_for_consensus

    @abstractmethod
    def parse_response(self, response: requests.Response) -> Union[Any, None]:
        """
        Parse the response and return a string.
        If there was an exception, return None.
        """
        pass

    def get_consensus_metric(self, client_instances: list[ClientInstance]) -> NodeWatchResult:
        """
        Tries max_retries_for_consensus times to get the same response from all
        instances.
        """
        for attempt in range(self.max_retries_for_consensus):
            results: dict[str, list[ClientInstance]] = {}
            unreachable_clients: list[ClientInstance] = []
            invalid_response_clients: list[ClientInstance] = []
            for client, api_future in perform_batched_request(self.request, client_instances).items():
                # reset the query list
                response: Union[requests.Response, Exception] = api_future.result()
                if not self.request.is_valid(response):
                    unreachable_clients.append(client)
                else:
                    result_as_str = self.parse_response(response)
                    if result_as_str is None:
                        invalid_response_clients.append(client)
                    else:
                        if result_as_str not in results:
                            results[result_as_str] = []
                        results[result_as_str].append(client)

            # bail if we have consensus
            if len(results.keys()) == 1 and len(unreachable_clients) == 0 and len(invalid_response_clients) == 0:
                return NodeWatchResult(results, unreachable_clients, invalid_response_clients)
            logging.debug(
                f"Retrying to get consensus on heads. {attempt}/{self.max_retries_for_consensus}: found {len(results.keys())} forks.")
        # we didn't get consensus, return last result
        return NodeWatchResult(results, unreachable_clients, invalid_response_clients)

    def result_as_log_str(self, metric_result: NodeWatchResult) -> str:
        """
        Returns a string representation of the result.
        """
        out = ""
        for result, clients in metric_result.results.items():
            out += f"{result}: {[client.name for client in clients]}\n"
        if len(metric_result.unreachable_clients) > 0:
            out += f"Unreachable clients: {[client.name for client in metric_result.unreachable_clients]}\n"
        if len(metric_result.invalid_response_clients) > 0:
            out += f"Value error clients: {[client.name for client in metric_result.invalid_response_clients]}\n"
        return out


class HeadsMetric(NodeWatchMetric):
    """
    A metric that returns the head slot, state root, and graffiti of each client instance, grouped by
    consensus among clients. Also reports unreachable clients and clients that returned an invalid response.
    """

    def __init__(self, max_retries: int, timeout: int, max_retries_for_consensus: int, last_n_root_bytes: int = 4):
        super().__init__(beacon_getBlockV2("head", max_retries=max_retries, timeout=timeout),
                         max_retries_for_consensus=max_retries_for_consensus, name="heads")
        self.last_n_root_bytes = last_n_root_bytes

    def parse_response(self, response: requests.Response) -> Union[tuple, None]:
        self.request: beacon_getBlockV2
        if not self.request.is_valid(response):
            return None
        else:
            try:
                block = self.request.get_block(response)
                slot = block["slot"]
                state_root = block["state_root"][-self.last_n_root_bytes*2:]
                graffiti = bytes.fromhex(block["body"]["graffiti"][2:]).decode(
                    "utf-8").replace(
                    "\x00", "")
                return slot, state_root, graffiti
            except Exception as e:
                logging.debug(f"Exception parsing response: {e}")
                return None

class CheckpointsMetric(NodeWatchMetric):
    """
    A metric that returns the finalized and justified checkpoints of each client instance, grouped by
    consensus among clients. Also reports unreachable clients and clients that returned an invalid response.
    """

    def __init__(self, max_retries: int, timeout: int, max_retries_for_consensus: int, last_n_root_bytes: int = 4):
        super().__init__(
            request=beacon_getFinalityCheckpoints(state_id="head", max_retries=max_retries, timeout=timeout),
            max_retries_for_consensus=max_retries_for_consensus, name="checkpoints")
        self.last_n_root_bytes = last_n_root_bytes

    def parse_response(self, response: requests.Response) -> Union[str, None]:
        self.request: beacon_getFinalityCheckpoints
        if not self.request.is_valid(response):
            return None
        else:
            try:
                finalized_checkpoint: tuple[int, str] = self.request.get_finalized_checkpoint(response)
                finalized_checkpoint_epoch = finalized_checkpoint[0]
                finalized_checkpoint_root = finalized_checkpoint[1]
                finalized_checkpoint_repr = f"({finalized_checkpoint_epoch}, 0x{finalized_checkpoint_root[-self.last_n_root_bytes * 2:]})"
                current_justified_checkpoint: tuple[int, str] = self.request.get_current_justified_checkpoint(response)
                current_justified_checkpoint_epoch = current_justified_checkpoint[0]
                current_justified_checkpoint_root = current_justified_checkpoint[1]
                current_justified_checkpoint_repr = f"({current_justified_checkpoint_epoch}, 0x{current_justified_checkpoint_root[-self.last_n_root_bytes * 2:]})"
                previous_justified_checkpoint: tuple[int, str] = self.request.get_previous_justified_checkpoint(
                    response)
                previous_justified_checkpoint_epoch = previous_justified_checkpoint[0]
                previous_justified_checkpoint_root = previous_justified_checkpoint[1]
                previous_justified_checkpoint_repr = f"({previous_justified_checkpoint_epoch}, 0x{previous_justified_checkpoint_root[-self.last_n_root_bytes * 2:]})"
                return f"finalized: {finalized_checkpoint_repr}, current justified: {current_justified_checkpoint_repr}, previous justified: {previous_justified_checkpoint_repr}"

            except Exception as e:
                logging.debug(f"Exception parsing response: {e}")
                return None


class HeadsAndCheckpointsMonitorAction(TestnetMonitorAction):
    """
    A TestnetMonitorAction that runs each slot and reports the heads and checkpoints of each
    client instance. We try multiple times to fetch the heads to reach consensus.
    These are grouped into one action to allow us to run the requests in parallel.
    """

    def __init__(self, client_instances: list[ClientInstance], max_retries: int, timeout: int,
                 max_retries_for_consensus: int):
        """
        client_instances: a list of client instances to monitor.
        max_retries: the number of times to retry a request.
        timeout: the timeout for a request.
        max_retries_for_consensus: the number of times to retry to get consensus.
        """
        super().__init__(name="head_slots", interval=TestnetMonitorActionInterval.EVERY_SLOT)
        self.get_heads_metric = HeadsMetric(max_retries=max_retries, timeout=timeout,
                                            max_retries_for_consensus=max_retries_for_consensus)
        self.get_checkpoints_metric = CheckpointsMetric(max_retries=max_retries, timeout=timeout,
                                                        max_retries_for_consensus=max_retries_for_consensus)
        self.instances_to_monitor = client_instances

    def perform_action(self):
        """
        Perform the action of getting the heads and checkpoints of each client instance.
        """
        heads_metric_result = self.get_heads_metric.get_consensus_metric(self.instances_to_monitor)
        checkpoints_metric_result = self.get_checkpoints_metric.get_consensus_metric(self.instances_to_monitor)

        head_metric_as_str = self.get_heads_metric.result_as_log_str(heads_metric_result)
        checkpoint_metric_as_str = self.get_checkpoints_metric.result_as_log_str(checkpoints_metric_result)

        # these should always be the same. Just in case we separate though.
        heads_detected_forks = not len(heads_metric_result.results) == 1 and len(heads_metric_result.unreachable_clients) == 0 and len(heads_metric_result.invalid_response_clients) == 0
        checkpoint_detected_forks = not len(checkpoints_metric_result.results) == 1 and len(checkpoints_metric_result.unreachable_clients) == 0 and len(checkpoints_metric_result.invalid_response_clients) == 0

        if heads_detected_forks is False and checkpoint_detected_forks is False:
            logging.info(f"no forks detected.")
        else:
            logging.info(f"detected {max(len(heads_metric_result.results)-1, len(checkpoints_metric_result.results)-1)} forks.")
        logging.info("heads:")
        logging.info(self.get_heads_metric.result_as_log_str(heads_metric_result))
        logging.info("checkpoints:")
        logging.info(self.get_checkpoints_metric.result_as_log_str(checkpoints_metric_result))


# class GetNetworkStatusMonitorAction(TestnetMonitorAction):
#     """
#     A TestnetMonitorAction that runs each slot and reports the heads of each
#     client instance. We try multiple times to fetch the heads to reach consensus
#     just in case some clients are slightly behind.
#     """
#
#     def __init__(self, client_instances: list[ClientInstance], max_retries: int, timeout: int,
#                  max_retries_for_consensus: int):
#         """
#         client_instances: a list of client instances to monitor.
#         max_retries: the number of times to retry a request.
#         timeout: the timeout for a request.
#         max_retries_for_consensus: the number of times to retry to get consensus.
#         """
#         super().__init__(name="head_slots", interval=TestnetMonitorActionInterval.EVERY_SLOT)
#         self.get_heads_metric = HeadsMetric(max_retries=max_retries, timeout=timeout,
#                                             max_retries_for_consensus=max_retries_for_consensus)
#         self.instances_to_monitor = client_instances
#
#     def perform_action(self):
#         """
#         Logs the head_slot, head_state_root and head_graffiti for each client instance.
#         grouped by consensus among the client instances. Also logs the unreachable
#         clients and clients we failed to parse the results from.
#         """
#         heads_metric_result = self.get_heads_metric.get_consensus_metric(self.instances_to_monitor)
#         logging.info(self.get_heads_metric.result_as_log_str(heads_metric_result))
#

class NodeWatch(object):
    def __init__(self, etb_config: ETBConfig, max_retries: int, timeout: int, max_retries_for_consensus: int = 3):
        """
        etb_config: the ETBConfig for the experiment.
        max_retries: the number of times to retry a request for a single client.
        timeout: the timeout for the requests.
        max_retries_for_consensus: the number of times to retry a series of requests to get consensus among all clients.
        """
        self.etb_config = etb_config
        self.max_retries = max_retries
        self.timeout = timeout
        self.testnet_monitor = TestnetMonitor(etb_config=self.etb_config)
        self.instances_to_monitor = self.etb_config.get_client_instances()

        status_action = HeadsAndCheckpointsMonitorAction(client_instances=self.instances_to_monitor,
                                                            max_retries=self.max_retries,
                                                            timeout=self.timeout,
                                                            max_retries_for_consensus=max_retries_for_consensus)

        self.testnet_monitor.add_action(status_action)

    def get_testnet_info_str(self) -> str:
        """
        Returns str with some information about the running experiment
        @return: str
        """
        out = ""
        out += f"genesis time: {self.etb_config.genesis_time}\n"
        out += f"genesis fork version: {self.etb_config.testnet_config.consensus_layer.get_genesis_fork()}\n"

        plausible_forks: list[ConsensusFork] = [
            self.etb_config.testnet_config.consensus_layer.capella_fork,
            self.etb_config.testnet_config.consensus_layer.deneb_fork,
            self.etb_config.testnet_config.consensus_layer.sharding_fork
        ]

        for fork in plausible_forks:
            if fork.epoch > 0 and fork.epoch != Epoch.FarFuture.value:
                out += f"\tScheduled fork {fork.name} at epoch: {fork.epoch}\n"

        out += f"client instances in testnet:\n"
        for instance in self.etb_config.get_client_instances():
            out += f"\t{instance.name} @ {instance.ip_address}\n"
            out += f"\t\tconsensus_client: {instance.consensus_config.client}, execution_client: {instance.execution_config.client}\n"
        return out

    def run(self):
        """
        Run the node watch printing out the results every slot.
        @return:
        """
        logging.info(self.get_testnet_info_str())
        self.testnet_monitor.run()
        # while True:
        #     # wait for the next slot
        #     goal_slot = self.testnet_monitor.get_slot() + 1
        #     self.testnet_monitor.wait_for_slot(goal_slot)
        #     logging.info(f"Expected slot: {goal_slot}")
        #     # logging.info(self.get_forks_str())
        #     self.show_status(max_retries_for_consensus=3)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Monitor the head and finality checkpoints of a testnet.")
    parser.add_argument("--log-level", type=str, default="info", help="Logging level")
    parser.add_argument("--max-retries", dest="max_retries", type=int, default=3, help="Max number of retries before "
                                                                                       "considering a node unreachable.")

    parser.add_argument("--request-timeout", dest="request_timeout", type=int, default=1,
                        help="Timeout for requests to nodes. Note that this "
                             "is a timeout for each request, e.g. for one "
                             "node we may wait timeout*max_retries seconds.")

    parser.add_argument("--delay", dest="delay", type=int, default=10, help="Delay before running the monitor.")

    args = parser.parse_args()

    time.sleep(args.delay)  # if the user is attaching to this instance give them time to do so.

    create_logger(name="node_watch", log_level=args.log_level.upper(), log_to_file=True)

    logging.info("Getting view of the testnet from etb-config.")
    etb_config: ETBConfig = get_etb_config()

    node_watcher = NodeWatch(etb_config=etb_config, max_retries=args.max_retries,
                             timeout=args.request_timeout)

    logging.info("Starting node watch.")
    node_watcher.run()
