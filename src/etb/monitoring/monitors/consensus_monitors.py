"""
ConsensusMonitors provide a generic interface that allows you to
create and run various metrics.

The metric defines:
    - measure_metric: A method that given a client, takes a measurement.
    - collect_metrics: Defines how to collect the measurements from the clients.
    - report_metric: Creates a report for the metric.
"""
import asyncio
from abc import abstractmethod
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Union, Any, Callable, Optional
import logging

import requests

from ...config.etb_config import ClientInstance
from ...interfaces.client_request import (
    ClientInstanceRequest,
    perform_batched_request,
    BeaconAPIgetBlockV2,
    BeaconAPIgetFinalityCheckpoints,
    BeaconAPIgetPeers,
    BeaconAPIgetIdentity,
)

"""
Consensus Monitors are meant to be standalone actions that can be performed
by a testnet_monitor or any other module.
"""

# The client instance and the result of the metric
ClientMonitorResult = dict[ClientInstance, Any]
# The result of the metric and the clients that returned that result
ConsensusMonitorResult = dict[Any, list[ClientInstance]]
# results are grouped by client, unreachable_clients, invalid_response_clients
ClientMonitorReport = tuple[
    ClientMonitorResult, list[ClientInstance], list[ClientInstance]
]
# clients grouped by result, unreachable_clients, invalid_response_clients
ConsensusMonitorReport = tuple[
    ConsensusMonitorResult, list[ClientInstance], list[ClientInstance]
]


class ClientMetricMonitor:
    """
    A monitor that can be run on a testnet.

    Provides a small interface to perform a query async on a client.

    A client query should:
        return an exception if we couldn't get a response from the client.
        return Any if got a response from the client.

    A response_parser should give the response of the query:
        return the parsed result.
        return None if the response is invalid.

    After each run the monitor will populate the following fields:
        - results: A dictionary of results grouped by result. {ClientInstance: Any [result]}
        - unreachable_clients: A list of clients that were unreachable.
        - invalid_response_clients: A list of clients that returned an invalid response.

    A report_metric routine is implemented by the user to report the metric.
    """

    def __init__(
        self,
        client_query: Callable[[ClientInstance], Union[Exception, Any]],
        response_parser: Callable[[Any], Optional[Any]],
        max_retries: int = 3,  # the max amount of time to retry a client
    ):
        self.client_query = client_query
        self.response_parser = response_parser
        self.max_retries = max_retries

        self.results: ClientMonitorResult = {}
        self.unreachable_clients: list[ClientInstance] = []
        self.invalid_response_clients: list[ClientInstance] = []

    def _clear_results(self):
        """clear the results of the monitor"""
        self.results = {}
        self.unreachable_clients = []
        self.invalid_response_clients = []

    def query_clients_for_metric(self, clients_to_monitor: list[ClientInstance]):
        """Query the clients for the metric.
        This will run the client_query on each client we are monitoring.
        If we get unreachable clients/invalid responses we will retry them
           until we get a valid response or we reach max_retries.
        """
        client_futures = {}
        with ThreadPoolExecutor(max_workers=len(clients_to_monitor)) as executor:
            for client in clients_to_monitor:
                client_futures[client] = executor.submit(self.client_query, client)

        # iterate through the futures and group them by result, unreachable, invalid_response
        for client, future in client_futures.items():
            result = future.result()
            # connection error
            if isinstance(result, Exception):
                self.unreachable_clients.append(client)
                continue

            parsed_result = self.response_parser(result)
            # parsing error
            if parsed_result is None:
                self.invalid_response_clients.append(client)
                continue
            # good response
            self.results[client] = parsed_result

    def report_metric(self) -> str:
        """Report the results obtained from the measurements."""
        out = ""
        for client, result in self.results.items():
            out += f"{client}: {result}\n"
        if len(self.unreachable_clients) > 0:
            out += f"Unreachable Clients: {[client.name for client in self.unreachable_clients]}\n"
        if len(self.invalid_response_clients) > 0:
            out += f"Invalid Response Clients: {[client.name for client in self.invalid_response_clients]}\n"
        return out

    def collect_metrics(self, clients_to_monitor: list[ClientInstance]):
        """Collect the metrics from the clients.
        This will run the client_query on each client we are monitoring, we retry
        until we get a valid response or we reach max_retries.
        """
        for _ in range(self.max_retries):
            self._clear_results()
            self.query_clients_for_metric(clients_to_monitor)
            if (
                len(self.unreachable_clients) == 0
                and len(self.invalid_response_clients) == 0
            ):
                return

    def run(self, clients_to_monitor: list[ClientInstance]) -> str:
        """Run the monitor."""
        self.collect_metrics(clients_to_monitor)
        return self.report_metric()


class ConsensusMetricMonitor(ClientMetricMonitor):
    """
    A monitor that can be run on a testnet.

    Provides a small interface to perform a query async on a client.

    A client query should:
        return an exception if we couldn't get a response from the client.
        return Any if got a response from the client.

    A response_parser should given the response of the query:
        return the parsed result.
        return None if the response is invalid.

    A report_metric routine is implemented by the user to report the metric.

    The monitor will attempt to query the clients (max_retries_for_consensus) times
    until it gets a consensus.

    After each run the monitor will populate the following fields:
        - results: A dictionary of results grouped by result. {Any [result]: list[ClientInstance]}
        - unreachable_clients: A list of clients that were unreachable.
        - invalid_response_clients: A list of clients that returned an invalid response.
    """

    def __init__(
        self,
        client_query: Callable[[ClientInstance], Union[Exception, Any]],
        response_parser: Callable[[Any], Optional[Any]],
        max_retries: int = 3,
        max_retries_for_consensus: int = 3,
    ):

        super().__init__(client_query, response_parser)
        self.max_retries_for_consensus = max_retries_for_consensus
        self.consensus_results: ConsensusMonitorResult = {}

    def _clear_results(self):
        """clear the results of the monitor"""
        super()._clear_results()
        self.consensus_results = {}

    def _reached_consensus(self) -> bool:
        """Check if we reached consensus."""
        return (
            len(self.results) == 1
            and len(self.unreachable_clients) == 0
            and len(self.invalid_response_clients) == 0
        )

    def order_results_by_consensus(self) -> ConsensusMonitorResult:
        """
        Query the clients for the result.
        """
        consensus_results: ConsensusMonitorResult = {}
        for client, result in self.results.items():
            if result not in consensus_results:
                consensus_results[result] = []
            consensus_results[result].append(client)

        return consensus_results

    def report_metric(self) -> str:
        """Report the results obtained from the measurements."""
        out = ""
        for result, clients in self.consensus_results.items():
            out += f"{result}: {[client.name for client in clients]}\n"
        if len(self.unreachable_clients) > 0:
            out += f"Unreachable Clients: {[client.name for client in self.unreachable_clients]}\n"
        if len(self.invalid_response_clients) > 0:
            out += f"Invalid Response Clients: {[client.name for client in self.invalid_response_clients]}\n"
        return out

    def collect_metrics(self, clients_to_monitor: list[ClientInstance]):
        """Collect the metrics from the clients.
        This will run the client_query on each client we are monitoring, we retry
        until we get consensus or we reach max_retries_for_consensus.
        """
        for _ in range(self.max_retries_for_consensus):
            self._clear_results()
            self.query_clients_for_metric(clients_to_monitor)
            self.consensus_results = self.order_results_by_consensus()
            if self._reached_consensus():
                return

    def run(self, clients_to_monitor: list[ClientInstance]) -> str:
        """Run the monitor."""
        self.collect_metrics(clients_to_monitor)
        return self.report_metric()


ClientHead = tuple[int, str, str]


class HeadsMonitor(ConsensusMetricMonitor):
    """
    A monitor that reports the heads of the clients.
    It will retry the query up to max_retries_for_consensus times.
    """

    def __init__(
        self, max_retries: int = 3, timeout: int = 5, max_retries_for_consensus: int = 3
    ):
        self.query = BeaconAPIgetBlockV2(max_retries=max_retries, timeout=timeout)
        self.max_retry_for_consensus = max_retries_for_consensus

        super().__init__(
            client_query=self.query.perform_request,
            response_parser=self._get_client_head_from_block,
        )

    def _get_client_head_from_block(
        self, response: requests.Response
    ) -> Optional[ClientHead]:
        try:
            block = self.query.get_block(response)
            slot = block["slot"]
            state_root = f'0x{block["state_root"][-8:]}'
            graffiti = (
                bytes.fromhex(block["body"]["graffiti"][2:])
                .decode("utf-8")
                .replace("\x00", "")
            )
            return slot, state_root, graffiti
        except Exception as e:
            logging.debug(f"Exception parsing response: {e}")
            return None

    def report_metric(self) -> str:
        """Report the results obtained from the measurements."""
        out = f"num_forks: {len(self.consensus_results) - 1}\n"
        out += super().report_metric()
        return out


# (epoch, root)
Checkpoint = tuple[int, str]
# finalized, justified, previous_justified
Checkpoints = tuple[Checkpoint, Checkpoint, Checkpoint]


class CheckpointsMonitor(ConsensusMetricMonitor):
    def __init__(
        self, max_retries: int = 3, timeout: int = 5, max_retries_for_consensus: int = 3
    ):
        self.query = BeaconAPIgetFinalityCheckpoints(
            max_retries=max_retries, timeout=timeout
        )
        self.max_retry_for_consensus = max_retries_for_consensus

        super().__init__(
            client_query=self.query.perform_request,
            response_parser=self._get_checkpoints,
        )

    def _get_checkpoints(self, response: requests.Response) -> Optional[str]:
        try:
            # checkpoints
            finalized_cp: tuple[int, str]
            current_justified_cp: tuple[int, str]
            previous_justified_cp: tuple[int, str]

            finalized_cp = self.query.get_finalized_checkpoint(response)
            fc_epoch = finalized_cp[0]
            fc_root = f"0x{finalized_cp[1][-8:]}"
            fc = (fc_epoch, fc_root)

            current_justified_cp = self.query.get_current_justified_checkpoint(response)
            cj_epoch = current_justified_cp[0]
            cj_root = f"0x{current_justified_cp[1][-8:]}"
            cj = (cj_epoch, cj_root)

            previous_justified_cp = self.query.get_previous_justified_checkpoint(
                response
            )
            pj_epoch = previous_justified_cp[0]
            pj_root = f"0x{previous_justified_cp[1][-8:]}"
            pj = (pj_epoch, pj_root)

            return f"finalized: {fc}, current justified: {cj}, previous justified: {pj}"

        except Exception as e:
            logging.debug(f"Exception parsing response: {e}")
            return None


# peer_id : {state: "", direction: ""}
PeerSummary = dict[str, dict[str, str]]


class PeeredClient:
    """
    A peered client summary
    """

    def __init__(self, peer_id: str, state: str, direction: str):
        self.peer_id = peer_id
        self.state = state
        self.direction = direction

    def __str__(self):
        return (
            f"peer_id: {self.peer_id}, state: {self.state}, direction: {self.direction}"
        )

    def __repr__(self):
        return self.__str__()


class ConsensusLayerPeersMonitor(ClientMetricMonitor):
    """
    A monitor that reports the peers of the clients.
    It will retry the query up to max_retries_for_consensus times.
    """

    def __init__(self, max_retries: int = 3, timeout: int = 5):
        self.query = BeaconAPIgetPeers(
            max_retries=max_retries, timeout=timeout, states=["connected"]
        )

        super().__init__(
            client_query=self.query.perform_request,
            response_parser=self._get_client_peers,
            max_retries=max_retries,
        )

    def _get_client_peers(self, response: requests.Response) -> Optional[dict]:
        peers_summary = {}
        try:
            peers = self.query.get_peers(response)
            for peer in peers:
                peers_summary[peer["peer_id"]] = PeeredClient(
                    peer_id=peer["peer_id"],
                    state=peer["state"],
                    direction=peer["direction"],
                )
            return peers_summary
        except Exception as e:
            logging.debug(f"Exception parsing response: {e}")
            return None


class ConsensusLayerIdentityMonitor(ClientMetricMonitor):
    """
    A monitor that reports the identity of the clients.
    """

    def __init__(self, max_retries: int = 3, timeout: int = 5):
        self.query = BeaconAPIgetIdentity(max_retries=max_retries, timeout=timeout)

        super().__init__(
            client_query=self.query.perform_request,
            response_parser=self._get_peer_id,
            max_retries=max_retries,
        )

    def _get_identity(self, response: requests.Response) -> Optional[dict]:
        try:
            identity = self.query.get_identity(response)
            return identity
        except Exception as e:
            logging.debug(f"Exception parsing response: {e}")
            return None

    def _get_peer_id(self, response: requests.Response) -> Optional[str]:
        try:
            peer_id = self.query.get_peer_id(response)
            return peer_id
        except Exception as e:
            logging.debug(f"Exception parsing response: {e}")
            return None


class ConsensusLayerPeeringSummary:
    """
    A summary of the consensus layer peering status.
    """

    def __init__(self, max_retries: int = 3, timeout: int = 5):
        self.max_retries = max_retries
        self.timeout = timeout
        # the peers for each client
        self.peers_monitor = ConsensusLayerPeersMonitor(
            max_retries=max_retries, timeout=timeout
        )
        self.identity_monitor = ConsensusLayerIdentityMonitor(
            max_retries=max_retries, timeout=timeout
        )

    def run(self, clients_to_monitor: list[ClientInstance]) -> str:
        """Run the monitor."""
        self.peers_monitor.collect_metrics(clients_to_monitor)
        self.identity_monitor.collect_metrics(clients_to_monitor)

        # better summary
        # mapping to go from peer_id to ClientInstance
        peer_id_client_map: dict[str, ClientInstance] = {}
        client_peer_id_map: dict[ClientInstance, str] = {}
        for client, identity in self.identity_monitor.results.items():
            peer_id_client_map[identity] = client
            client_peer_id_map[client] = identity

        out = ""
        inbound_peer_map: dict[ClientInstance, list[Union[ClientInstance, str]]] = {}
        outbound_peer_map: dict[ClientInstance, list[Union[ClientInstance, str]]] = {}
        for client, peered_clients in self.peers_monitor.results.items():
            if client not in inbound_peer_map:
                inbound_peer_map[client] = []
            if client not in outbound_peer_map:
                outbound_peer_map[client] = []
            for _, peered_client in peered_clients.items():
                if peered_client.peer_id in peer_id_client_map:
                    peered_client_name = peer_id_client_map[peered_client.peer_id].name
                else:
                    peered_client_name = peered_client.peer_id
                if peered_client.direction == "inbound":
                    inbound_peer_map[client].append(peered_client_name)
                elif peered_client.direction == "outbound":
                    outbound_peer_map[client].append(peered_client_name)
        for client in clients_to_monitor:
            out += f"{client.name}:\n"
            out += f"\tinbound: {inbound_peer_map[client]}\n"
            out += f"\toutbound: {outbound_peer_map[client]}\n"

        return out
