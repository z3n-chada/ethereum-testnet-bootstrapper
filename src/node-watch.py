"""
    A simple TestnetAction that reports the current:
        head slot (number, root, graffiti) graffiti will default to proposer instance
        finality checkpoints: (current_justified, finalized) (epoch, root)

    The output is organized in terms of forks seen. Roots are represented by
    the last 6 characters of the root.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed, Future
import logging
import time
from typing import Union, Any

import requests

from etb.common.Consensus import ConsensusFork, Epoch
from etb.common.Utils import create_logger, logging_levels
from etb.config.ETBConfig import ETBConfig, ClientInstance, get_etb_config
from etb.interfaces.TestnetMonitor import TestnetMonitor
from etb.interfaces.ClientRequest import beacon_getBlockV2, perform_batched_request




def perform_query(query, max_retries=3, timeout=5) -> Union[Any, Exception]:
    """
    Perform a query to the API endpoint.
    @param query: query to perform
    @param max_retries: max number of retries
    @param timeout: timout per query
    @return:
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(query, timeout=timeout)
            response.raise_for_status()

            # Process the response data here
            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                logger.debug(f"RequestException occurred during the API request {query}")
                logger.debug("Retrying...")
            else:
                logger.error(f"Maximum number of retries reached for {query}")
                return e

        except ValueError as e:
            logger.error(f"Error occurred while processing the response data for {query}")
            return e


class NodeWatch(object):
    def __init__(self, etb_config: ETBConfig, max_retries: int, timeout: int):
        self.etb_config = etb_config
        self.max_retries = max_retries
        self.timeout = timeout
        self.testnet_monitor = TestnetMonitor(etb_config=self.etb_config)
        self.instances_to_monitor = self.etb_config.get_client_instances()

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

    def get_forks_str(self) -> str:
        """
        Returns a string suitable to report the current heads of all clients.
        @return:
        """
        out = ""
        heads, unreachable_instances, value_error_instances = self._get_heads(max_retries_for_consensus=2)
        forks = {}
        for result_tuple, clients in heads.items():
            head = result_tuple[0]
            state_root = result_tuple[1][-6:]  # last 6 bytes of the state root
            graffiti = result_tuple[2]
            if (head, state_root, graffiti) not in forks:
                forks[(head, state_root, graffiti)] = []
            for client in clients:
                forks[(head, state_root, graffiti)].append(client.name)
        out += f"Current forks: {len(forks) - 1}\n"
        for fork, clients in forks.items():
            out += f"head_slot:{fork[0]}, state_root:{fork[1]}, graffiti:{fork[2]}, clients: {clients}\n"
        if len(unreachable_instances) > 0:
            out += f"Unreachable instances: {unreachable_instances}\n"
        if len(value_error_instances) > 0:
            out += f"Failed to parse message from: {value_error_instances}\n"

        return out

    def _get_heads(self, max_retries_for_consensus: int) -> tuple[
        dict[tuple[int, str, str], list[ClientInstance]], list[ClientInstance], list[ClientInstance]]:
        """
        Returns a 3-tuple given by:
        1. dict: {(slot, root, graffiti) : [clients]} where block is the head block
        2. list: unreachable clients
        3. list: clients that had an error unpacking the block.

        If there is not consensus w.r.t heads it will try max_retries_for_consensus times
        in case the clients just needed to catch up. e.g. half are one slot behind on the
        canonical chain.
        @return:
        """

        # TODO this does the retries naively. Only retry clients with lower head slot.

        get_head_request = beacon_getBlockV2(block="head", max_retries=self.max_retries, timeout=self.timeout)

        clients_to_query = [x for x in self.instances_to_monitor]

        for attempt in range(max_retries_for_consensus):
            results: dict[tuple[int, str, str], list[ClientInstance]] = {}
            unreachable_clients: list[ClientInstance] = []
            value_error_clients: list[ClientInstance] = []
            for client, api_future in perform_batched_request(get_head_request, clients_to_query).items():
                # reset the query list
                response: Union[requests.Response, Exception] = api_future.result()
                if not get_head_request.is_valid(response):
                    unreachable_clients.append(client)
                else:
                    try:
                        block = get_head_request.get_block(response)
                        slot = block["slot"]
                        state_root = block["state_root"]
                        graffiti = bytes.fromhex(block["body"]["graffiti"][2:]).decode(
                            "utf-8").replace(
                            "\x00", "")
                        _tuple = (slot, state_root, graffiti)
                    except Exception as e:
                        logging.error(f"Failed to unpack result head block response from {client.name}")
                        value_error_clients.append(client)
                        continue
                    if _tuple in results:
                        results[_tuple].append(client)
                    else:
                        results[_tuple] = [client]
            # bail if we have consensus
            if len(results.keys()) == 1:
                return results, unreachable_clients, value_error_clients
            logging.debug(f"Retrying to get consensus on heads. {attempt}/{max_retries_for_consensus}: found {len(results.keys())} forks.")

        return results, unreachable_clients, value_error_clients

    def run(self):
        """
        Run the node watch printing out the results every slot.
        @return:
        """
        logging.info(self.get_testnet_info_str())

        while True:
            # wait for the next slot
            goal_slot = self.testnet_monitor.get_slot() + 1
            self.testnet_monitor.wait_for_slot(goal_slot)
            logging.info(f"Expected slot: {goal_slot}")
            logging.info(self.get_forks_str())

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
