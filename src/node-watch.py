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
from etb.common.Utils import get_logger, logging_levels
from etb.config.ETBConfig import ETBConfig, ClientInstance, get_etb_config

logger: logging.Logger = get_logger(name="NodeWatch", log_level="info")


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


class SimpleNodeWatch(object):
    def __init__(self, logger: logging.Logger, etb_config: ETBConfig, max_retries: int, timeout: int):
        self.logger: logging.Logger = logger
        self.etb_config: ETBConfig = etb_config
        self.max_retries: int = max_retries
        self.timeout: int = timeout

        self.instances_to_monitor = self.etb_config.get_client_instances()

        self.queries: dict[ClientInstance, list[str]] = {}
        for instance in self.instances_to_monitor:
            self.queries[instance] = []
            self.queries[instance].append(f"{instance.get_consensus_beacon_api_path()}/eth/v2/beacon/blocks/head")

        # get the genesis time so we can calculate slot offsets.
        self.genesis_time = self.etb_config.genesis_time

    def wait_for_slot(self, slot: int, interval: int = 1):
        """
        Wait until the current slot is equal to the target slot.
        @param slot: target slot to wait for
        @param interval: max interval between sleeps
        @return: when current time corresponds to the target slot
        """
        target_time = self.etb_config.slot_to_time(slot)

        while int(time.time()) < target_time:
            self.logger.debug(f"Waiting for slot {slot}")
            time.sleep(min(interval, target_time - int(time.time())))

    def get_node_status(self):
        """
        Get the head and finality checkpoints for each node.
        @return:
        """
        status_requests = [
            "/eth/v2/beacon/blocks/head",
        ]
        value_error_instances = []
        unreachable_instances = []
        results = {}

        # Create a ThreadPoolExecutor with a maximum of 5 concurrent threads
        with ThreadPoolExecutor(max_workers=len(self.instances_to_monitor)) as executor:
            head_futures: dict[ClientInstance, Future] = {}

            for client_instance in self.instances_to_monitor:
                query = f"{client_instance.get_consensus_beacon_api_path()}/eth/v2/beacon/blocks/head"
                future = executor.submit(perform_query, query, max_retries=self.max_retries, timeout=self.timeout)
                head_futures[client_instance] = future

            # Retrieve the results as they become available and organize the responses
            for client_instance, future in head_futures.items():
                response = future.result()
                if isinstance(response, requests.RequestException):
                    unreachable_instances.append(client_instance.name)
                elif isinstance(response, ValueError):
                    value_error_instances.append(client_instance.name)
                else:
                    try:
                        head = response["data"]["message"]["slot"]
                        state_root = response["data"]["message"]["state_root"]
                        graffiti = bytes.fromhex(response["data"]["message"]["body"]["graffiti"][2:]).decode(
                            "utf-8").replace(
                            "\x00", "")
                        results[client_instance] = (head, state_root, graffiti)
                    except ValueError:
                        value_error_instances.append(client_instance.name)
                    except KeyError:
                        value_error_instances.append(client_instance.name)

        # separate the forks
        forks = {}
        for client_instance, result in results.items():
            head = result[0]
            state_root = result[1][-6:]  # last 6 bytes of the state root
            graffiti = result[2]
            if (head, state_root, graffiti) not in forks:
                forks[(head, state_root, graffiti)] = []
            forks[(head, state_root, graffiti)].append(client_instance.name)
        # print results to the logger
        self.logger.info(f"Current forks: {len(forks) - 1}")
        for fork, clients in forks.items():
            self.logger.info(f"view: head_slot:{fork[0]}, state_root:{fork[1]}, graffiti:{fork[2]}, clients: {clients}")
        self.logger.info(f"Unreachable instances: {unreachable_instances}")
        if len(value_error_instances) > 0:
            self.logger.info(f"Failed to parse message from: {value_error_instances}")

    def get_testnet_info(self) -> str:
        """
            Prints some information about the running experiment
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
        curr_slot = 1
        self.logger.info(f"Testnet info: \n{self.get_testnet_info()}")

        while True:
            self.wait_for_slot(curr_slot)
            self.logger.info(
                f"Status for expected slot: {curr_slot} (epoch: {self.etb_config.slot_to_epoch(curr_slot)})")
            self.get_node_status()
            curr_slot += 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Monitor the head and finality checkpoints of a testnet.")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    parser.add_argument("--max-retries", dest="max_retries", type=int, default=3, help="Max number of retries before "
                                                                                       "considering a node unreachable.")

    parser.add_argument("--request-timeout", dest="request_timeout", type=int, default=1,
                        help="Timeout for requests to nodes. Note that this "
                             "is a timeout for each request, e.g. for one "
                             "node we may wait timeout*max_retries seconds.")

    args = parser.parse_args()

    time.sleep(5)  # if the user is attaching to this instance give them time to do so.

    if args.log_level not in logging_levels:
        raise ValueError(f"Invalid logging level: {args.log_level} ({logging_levels.keys()})")
    logger.setLevel(logging_levels[args.log_level])

    logger.info("Getting view of the testnet from etb-config.")
    etb_config: ETBConfig = get_etb_config(logger)

    node_watcher = SimpleNodeWatch(logger=logger, etb_config=etb_config, max_retries=args.max_retries,
                                    timeout=args.request_timeout)
    logger.info("Starting node watch.")
    node_watcher.run()
