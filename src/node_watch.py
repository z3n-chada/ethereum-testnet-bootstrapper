"""
    A simple TestnetAction that reports the current:
        head slot (number, root, graffiti) graffiti will default to proposer instance
        finality checkpoints: (current_justified, finalized) (epoch, root)

    The output is organized in terms of forks seen. Roots are represented by
    the last 6 characters of the root.
"""
import logging
import time
from abc import abstractmethod
from typing import Union, Any

import requests

from etb.common.consensus import ConsensusFork, Epoch
from etb.common.utils import create_logger
from etb.config.etb_config import ETBConfig, ClientInstance, get_etb_config
from etb.interfaces.client_request import (
    BeaconAPIgetBlockV2,
    perform_batched_request,
    ClientInstanceRequest,
    BeaconAPIgetFinalityCheckpoints,
)
from etb.interfaces.testnet_monitor import (
    TestnetMonitor,
    TestnetMonitorAction,
    TestnetMonitorActionInterval,
)


class NodeWatchResult:
    """The result of a NodeWatchMetric.

    results: a dictionary of results, where the key is the result and the value is a list of client instances that returned that result.
    unreachable_clients: a list of client instances that were unreachable.
    invalid_response_clients: a list of client instances that returned an invalid response.
    """

    def __init__(
        self,
        results: dict[Any, list[ClientInstance]],
        unreachable_clients: list[ClientInstance],
        invalid_response_clients: list[ClientInstance],
    ):
        self.results = results
        self.unreachable_clients = unreachable_clients
        self.invalid_response_clients = invalid_response_clients


class NodeWatchMetric:
    """A metric to be captured across some client instances."""

    def __init__(
        self,
        request: ClientInstanceRequest,
        name: str,
        max_retries_for_consensus: int = 3,
    ):
        self.request = request
        self.name = name
        self.max_retries_for_consensus = max_retries_for_consensus

    @abstractmethod
    def parse_response(self, response: requests.Response) -> Union[Any, None]:
        """Parse the response and return a string.

        If there was an exception, return None.
        """
        pass

    def get_consensus_metric(
        self, client_instances: list[ClientInstance]
    ) -> NodeWatchResult:
        """Tries max_retries_for_consensus times to get the same response from
        all instances."""
        for attempt in range(self.max_retries_for_consensus):
            results: dict[str, list[ClientInstance]] = {}
            unreachable_clients: list[ClientInstance] = []
            invalid_response_clients: list[ClientInstance] = []
            for client, api_future in perform_batched_request(
                self.request, client_instances
            ).items():
                # reset the query list
                response: Union[requests.Response,
                                Exception] = api_future.result()
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
            if (
                len(results.keys()) == 1
                and len(unreachable_clients) == 0
                and len(invalid_response_clients) == 0
            ):
                return NodeWatchResult(
                    results, unreachable_clients, invalid_response_clients
                )
            # we didn't get consensus, log and retry
            progress = attempt / self.max_retries_for_consensus
            num_forks = len(results.keys()) - 1
            logging.debug(
                f"Retrying to get consensus on heads. {progress}: found {num_forks} forks."
            )
        # we didn't get consensus, return last result
        return NodeWatchResult(
            results, unreachable_clients, invalid_response_clients)

    def result_as_log_str(self, metric_result: NodeWatchResult) -> str:
        """Returns a string representation of the result."""
        out = ""
        for result, clients in metric_result.results.items():
            out += f"{result}: {[client.name for client in clients]}\n"
        if len(metric_result.unreachable_clients) > 0:
            unreachable_clients = [
                c.name for c in metric_result.unreachable_clients]
            out += f"Unreachable clients: {unreachable_clients}\n"
        if len(metric_result.invalid_response_clients) > 0:
            invalid_response_clients = [
                c.name for c in metric_result.invalid_response_clients
            ]
            out += f"Value error clients: {invalid_response_clients}\n"
        return out


class HeadsMetric(NodeWatchMetric):
    """A metric that returns the head slot, state root, and graffiti of each
    client instance, grouped by consensus among clients.

    Also reports unreachable clients and clients that returned an
    invalid response.
    """

    def __init__(
        self,
        max_retries: int,
        timeout: int,
        max_retries_for_consensus: int,
        last_n_root_bytes: int = 4,
    ):
        super().__init__(
            BeaconAPIgetBlockV2(
                "head",
                max_retries=max_retries,
                timeout=timeout),
            max_retries_for_consensus=max_retries_for_consensus,
            name="heads",
        )
        self.last_n_root_bytes = last_n_root_bytes

    def parse_response(
            self, response: requests.Response) -> Union[tuple, None]:
        self.request: BeaconAPIgetBlockV2
        if not self.request.is_valid(response):
            return None

        try:
            block = self.request.get_block(response)
            slot = block["slot"]
            state_root = block["state_root"][-self.last_n_root_bytes * 2:]
            graffiti = (
                bytes.fromhex(block["body"]["graffiti"][2:])
                .decode("utf-8")
                .replace("\x00", "")
            )
            return slot, state_root, graffiti
        except Exception as e:
            logging.debug(f"Exception parsing response: {e}")
            return None


class CheckpointsMetric(NodeWatchMetric):
    """A metric that returns the finalized and justified checkpoints of each
    client instance, grouped by consensus among clients.

    Also reports unreachable clients and clients that returned an
    invalid response.
    """

    def __init__(
        self,
        max_retries: int,
        timeout: int,
        max_retries_for_consensus: int,
        last_n_root_bytes: int = 4,
    ):
        super().__init__(
            request=BeaconAPIgetFinalityCheckpoints(
                state_id="head", max_retries=max_retries, timeout=timeout
            ),
            max_retries_for_consensus=max_retries_for_consensus,
            name="checkpoints",
        )
        self.last_n_root_bytes = last_n_root_bytes

    def parse_response(self, response: requests.Response) -> Union[str, None]:
        self.request: BeaconAPIgetFinalityCheckpoints
        if not self.request.is_valid(response):
            return None

        try:
            # checkpoints
            finalized_cp: tuple[int, str]
            current_justified_cp: tuple[int, str]
            previous_justified_cp: tuple[int, str]

            finalized_cp = self.request.get_finalized_checkpoint(response)
            fc_epoch = finalized_cp[0]
            fc_root = finalized_cp[1]
            fc_repr = f"({fc_epoch}, 0x{fc_root[-self.last_n_root_bytes * 2:]})"

            current_justified_cp = self.request.get_current_justified_checkpoint(
                response
            )
            cj_epoch = current_justified_cp[0]
            cj_root = current_justified_cp[1]
            cj_repr = f"({cj_epoch}, 0x{cj_root[-self.last_n_root_bytes * 2:]})"

            previous_justified_cp = self.request.get_previous_justified_checkpoint(
                response
            )
            pj_epoch = previous_justified_cp[0]
            pj_root = previous_justified_cp[1]
            pj_repr = f"({pj_epoch}, 0x{pj_root[-self.last_n_root_bytes * 2:]})"
            return f"finalized: {fc_repr}, current justified: {cj_repr}, previous justified: {pj_repr}"

        except Exception as e:
            logging.debug(f"Exception parsing response: {e}")
            return None


class HeadsAndCheckpointsMonitorAction(TestnetMonitorAction):
    """A TestnetMonitorAction that runs each slot and reports the heads and
    checkpoints of each client instance.

    We try multiple times to fetch the heads to reach consensus. These
    are grouped into one action to allow us to run the requests in
    parallel.
    """

    def __init__(
        self,
        client_instances: list[ClientInstance],
        max_retries: int,
        timeout: int,
        max_retries_for_consensus: int,
    ):
        """
        client_instances: a list of client instances to monitor.
        max_retries: the number of times to retry a request.
        timeout: the timeout for a request.
        max_retries_for_consensus: the number of times to retry to get consensus.
        """
        super().__init__(
            name="head_slots", interval=TestnetMonitorActionInterval.EVERY_SLOT
        )
        self.get_heads_metric = HeadsMetric(
            max_retries=max_retries,
            timeout=timeout,
            max_retries_for_consensus=max_retries_for_consensus,
        )
        self.get_checkpoints_metric = CheckpointsMetric(
            max_retries=max_retries,
            timeout=timeout,
            max_retries_for_consensus=max_retries_for_consensus,
        )
        self.instances_to_monitor = client_instances

    def perform_action(self):
        """Perform the action of getting the heads and checkpoints of each
        client instance."""
        heads_result = self.get_heads_metric.get_consensus_metric(
            self.instances_to_monitor
        )
        checkpoints_result = self.get_checkpoints_metric.get_consensus_metric(
            self.instances_to_monitor
        )

        head_metric_as_str = self.get_heads_metric.result_as_log_str(
            heads_result)
        checkpoint_metric_as_str = self.get_checkpoints_metric.result_as_log_str(
            checkpoints_result
        )

        # these should always be the same. Just in case we separate though.
        heads_detected_forks = (
            not len(heads_result.results) == 1
            and len(heads_result.unreachable_clients) == 0
            and len(heads_result.invalid_response_clients) == 0
        )
        checkpoint_detected_forks = (
            not len(checkpoints_result.results) == 1
            and len(checkpoints_result.unreachable_clients) == 0
            and len(checkpoints_result.invalid_response_clients) == 0
        )

        if heads_detected_forks is False and checkpoint_detected_forks is False:
            logging.info("no forks detected.")
        else:
            num_forks = (
                max(len(heads_result.results), len(
                    checkpoints_result.results)) - 1
            )
            logging.info(f"detected {num_forks} forks.")
        logging.info("heads:")
        logging.info(head_metric_as_str)
        logging.info("checkpoints:")
        logging.info(checkpoint_metric_as_str)


class NodeWatch:
    """
    A class that watches the nodes of a testnet and reports on their status.
    """

    def __init__(
        self,
        etb_config: ETBConfig,
        max_retries: int,
        timeout: int,
        max_retries_for_consensus: int = 3,
    ):
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

        status_action = HeadsAndCheckpointsMonitorAction(
            client_instances=self.instances_to_monitor,
            max_retries=self.max_retries,
            timeout=self.timeout,
            max_retries_for_consensus=max_retries_for_consensus,
        )

        self.testnet_monitor.add_action(status_action)

    def get_testnet_info_str(self) -> str:
        """Returns str with some information about the running experiment
        @return: str."""
        out = ""
        out += f"genesis time: {self.etb_config.genesis_time}\n"
        out += f"genesis fork version: {self.etb_config.testnet_config.consensus_layer.get_genesis_fork()}\n"

        plausible_forks: list[ConsensusFork] = [
            self.etb_config.testnet_config.consensus_layer.capella_fork,
            self.etb_config.testnet_config.consensus_layer.deneb_fork,
            self.etb_config.testnet_config.consensus_layer.sharding_fork,
        ]

        for fork in plausible_forks:
            if fork.epoch > 0 and fork.epoch != Epoch.FarFuture.value:
                out += f"\tScheduled fork {fork.name} at epoch: {fork.epoch}\n"

        out += "client instances in testnet:\n"
        for instance in self.etb_config.get_client_instances():
            out += f"\t{instance.name} @ {instance.ip_address}\n"
            out += f"\t\tconsensus_client: {instance.consensus_config.client}, execution_client: {instance.execution_config.client}\n"
        return out

    def run(self):
        """Run the node watch printing out the results every slot.

        @return:
        """
        logging.info(self.get_testnet_info_str())
        self.testnet_monitor.run()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Monitor the head and finality checkpoints of a testnet."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        help="Logging level")
    parser.add_argument(
        "--max-retries",
        dest="max_retries",
        type=int,
        default=3,
        help="Max number of retries before " "considering a node unreachable.",
    )

    parser.add_argument(
        "--request-timeout",
        dest="request_timeout",
        type=int,
        default=1,
        help="Timeout for requests to nodes. Note that this "
        "is a timeout for each request, e.g. for one "
        "node we may wait timeout*max_retries seconds.",
    )

    parser.add_argument(
        "--delay",
        dest="delay",
        type=int,
        default=10,
        help="Delay before running the monitor.",
    )

    args = parser.parse_args()

    time.sleep(
        args.delay
    )  # if the user is attaching to this instance give them time to do so.

    create_logger(
        name="node_watch",
        log_level=args.log_level.upper(),
        log_to_file=True)

    logging.info("Getting view of the testnet from etb-config.")
    etb_config: ETBConfig = get_etb_config()

    node_watcher = NodeWatch(
        etb_config=etb_config,
        max_retries=args.max_retries,
        timeout=args.request_timeout,
    )

    logging.info("Starting node watch.")
    node_watcher.run()
