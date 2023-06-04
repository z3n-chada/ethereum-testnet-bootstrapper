"""
    Class for interacting with the testnet. Provides stubs for performing
    actions at various stages of the testnet.
"""
import logging
import pathlib
import time
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
import random
from typing import Callable, Any

# from .BeaconAPI import perform_api_request_v2, APIRequestV2
from .ClientRequest import beacon_getGenesis
from .ETBConfig import ETBConfig, ClientInstance
from .UtilityWrappers import create_logger


class ActionIntervalType(Enum):
    ON_SLOT = 0  # run the action every X CL slots
    ON_EPOCH = 1  # run the action every X CL epochs
    ON_TIME = 2  # run the action every X seconds
    AT_SLOT = 3  # one time run at a CL slot
    AT_EPOCH = 4  # one time run at a CL epoch
    AT_TIME = 5  # one time run a a unix time


class ActionInterval(object):
    """
    When an action is run.
    """

    def __init__(self, interval_length: int, interval_type: ActionIntervalType):
        self.interval_length = interval_length
        self.interval_type = interval_type

    def __repr__(self) -> str:
        if self.interval_type is ActionIntervalType.ON_SLOT:
            return f"ActionInterval::every {self.interval_length} slots."
        elif self.interval_type is ActionIntervalType.ON_EPOCH:
            return f"ActionInterval::every {self.interval_length} epochs."
        elif self.interval_type is ActionIntervalType.ON_TIME:
            return f"ActionInterval::every {self.interval_length} seconds."
        elif self.interval_type is ActionIntervalType.AT_SLOT:
            return f"ActionInterval::once at slot {self.interval_length}"
        elif self.interval_type is ActionIntervalType.AT_EPOCH:
            return f"ActionInterval::once at epoch {self.interval_length}"
        elif self.interval_type is ActionIntervalType.AT_TIME:
            return f"ActionInterval::once at time {self.interval_length}"


class EverySlotInterval(ActionInterval):
    def __init__(self):
        super().__init__(1, ActionIntervalType.ON_SLOT)


class TestnetMonitorAction(object):
    """
    Represents an action that is run on the testnet.

    By default, we use a time based approach. e.g. if we do an action every slot we
    calculate the expected time of that slot.

    The time starts according to the bootstrap time. (when the testnet was launched.)
    CL_based actions will occur starting from the beacon genesis time.
    """

    def __init__(
        self,
        interval: ActionInterval,
        action: Callable[[Any], Any],
        targets: list[Any],
        delay=1,
    ):
        self.interval: ActionInterval = interval
        self.action = action
        self.targets = targets
        self.delay = delay

    def __repr__(self):
        return f"{self.action.__name__} : {self.interval}"

    def perform_action(self):
        with ThreadPoolExecutor(max_workers=len(self.targets)) as executor:
            results = executor.map(self.action, self.targets)
        return zip(self.targets, results)


def _action_proxy(action: TestnetMonitorAction):
    return action.perform_action()


class TestnetMonitor(object):
    """
    The testnet monitor just monitors the nodes and keeps track of time.

    You can use the monitor to wait for events, or register actions for
    events where it is suitable.
    """

    def __init__(self, etb_config: ETBConfig, logger: logging.Logger = None):
        self.etb_config: ETBConfig = etb_config

        if logger is None:
            self.logger = create_logger("testnet-monitor", "debug")
        else:
            self.logger = logger

        self.consensus_genesis_time: int = None
        self.seconds_per_slot = self.etb_config.preset_base.SECONDS_PER_SLOT.value
        self.slots_per_epoch = self.etb_config.preset_base.SLOTS_PER_EPOCH.value

        # actions we do once.
        self.one_time_actions: dict[int, list[TestnetMonitorAction]] = {}

        # actions we always do.
        self.repeated_actions: dict[str, list[TestnetMonitorAction]] = {
            "epoch": [],
            "slot": [],
        }

        self.current_slot: int = 0
        self.current_epoch: int = 0

        while not pathlib.Path(
            self.etb_config.files.get("consensus-checkpoint-file")
        ).exists():
            time.sleep(1)

        self._init()

    def _get_beaconchain_genesis(self, max_retries=5) -> int:

        cl_client = random.choice(self.etb_config.get_client_instances())
        curr_try = 0
        # allow a lot of time for all the clients to come up
        api_request = beacon_getGenesis(timeout=10)
        while curr_try != max_retries:
            curr_try += 1
            err = api_request.perform_request(cl_client)
            if api_request.valid_response:
                genesis = api_request.retrieve_response()
                return int(genesis["genesis_time"])

        self.logger.error(
            "Couldn't get genesis time from chain. Using bootstrap genesis time instead."
        )
        return self.etb_config.get_bootstrap_genesis_time()

    def _init(self):
        self.consensus_genesis_time = self._get_beaconchain_genesis()

    def get_slot(self) -> int:
        return (int(time.time()) - self.consensus_genesis_time) // self.seconds_per_slot

    def get_epoch(self):
        return self.get_slot() // self.slots_per_epoch

    def wait_for_slot(self, slot_num):
        while self.get_slot() < slot_num:
            t_delta = (slot_num - self.get_slot()) * self.seconds_per_slot
            sleep_time = min(60, t_delta)
            self.logger.debug(
                f"wait_for_slot: sleeping for {sleep_time} seconds. (curr_slot: {self.get_slot()} goal slot: {slot_num})"
            )
            time.sleep(sleep_time)
        return

    def wait_for_epoch(self, epoch_num):
        curr_slot = self.etb_config.epoch_to_slot(epoch_num)
        return self.wait_for_slot(curr_slot)

    def wait_for_next_slot(self):
        self.wait_for_slot(self.get_slot() + 1)

    def wait_for_next_epoch(self):
        self.wait_for_slot(self.etb_config.epoch_to_slot(self.get_epoch() + 1))

    def add_action(self, action: TestnetMonitorAction):
        """
        TODO: the goal of this is to allow for automated running of actions.
        :param action:
        :return:
        """
        interval_type = action.interval.interval_type

        if action.interval.interval_type is ActionIntervalType.ON_SLOT:
            self.repeated_actions["slot"].append(action)
        elif action.interval.interval_type is ActionIntervalType.ON_EPOCH:
            self.repeated_actions["epoch"].append(action)

        elif action.interval.interval_type is ActionIntervalType.AT_SLOT:
            self.one_time_actions["slot"][action.interval.interval_length].append(
                action
            )

        elif action.interval.interval_type is ActionIntervalType.AT_EPOCH:
            self.one_time_actions["slot"][
                self.etb_config.epoch_to_slot(action.interval.interval_length)
            ].append(action)

        else:
            # TODO.
            raise Exception("Not implemented")

    def _perform_actions(self, observed_slot: int):
        actions_to_do: list[TestnetMonitorAction] = [
            actions for actions in self.repeated_actions["slot"]
        ]
        if observed_slot % self.etb_config.preset_base.SLOTS_PER_EPOCH.value == 0:
            for actions in self.repeated_actions["epoch"]:
                actions_to_do.append(actions)

        if observed_slot in self.one_time_actions:
            for action in self.one_time_actions[observed_slot]:
                actions_to_do.append(action)

        with ThreadPoolExecutor(max_workers=len(actions_to_do)) as executor:
            results = executor.map(_action_proxy, actions_to_do)

        return zip(actions_to_do, results)

    def start(self):
        self.current_slot = self.get_slot()
        while True:
            self.wait_for_slot(self.get_slot() + 1)
            self.current_slot += 1
            # iterate
            for zipped_actions in self._perform_actions(self.current_slot + 1):
                action, zipped_results = zipped_actions
                self.logger.info(action)
                for client, result in zipped_results:
                    self.logger.info(result)
