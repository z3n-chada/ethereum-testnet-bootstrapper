"""TestnetMonitor interface.

Provides abstractions to monitor testnet progress.
"""
import logging
import time
from abc import abstractmethod
from enum import Enum

from ..config.etb_config import ETBConfig


class TestnetMonitorActionInterval(Enum):
    """An enum for the interval of an action."""

    EVERY_SLOT = 1
    EVERY_EPOCH = 2
    ONCE = 3


class TestnetMonitorAction:
    """An abstraction for an action to perform on a testnet at some
    interval."""

    def __init__(self, name: str, interval: TestnetMonitorActionInterval):
        self.interval: TestnetMonitorActionInterval = interval
        self.name = name

    @abstractmethod
    def perform_action(self):
        pass


class TestnetMonitor:
    """TestnetMonitor provides useful interfaces for monitoring the progress of
    the testnet.

    - get_slot: get the current slot
    - get_epoch: get the current epoch
    - wait_for_slot: wait until a target slot
    - wait_for_epoch: wait until a target epoch
    - slot_to_epoch: convert slot to epoch
    - epoch_to_slot: convert epoch to slot
    """

    def __init__(self, etb_config: ETBConfig):
        self.etb_config: ETBConfig = etb_config
        self.consensus_genesis_time: int = self.etb_config.genesis_time
        self.seconds_per_slot: int = (
            self.etb_config.testnet_config.consensus_layer.preset_base.SECONDS_PER_SLOT.value
        )
        self.slots_per_epoch: int = (
            self.etb_config.testnet_config.consensus_layer.preset_base.SLOTS_PER_EPOCH.value
        )

        self.current_slot: int = 0
        self.current_epoch: int = 0

        self.every_slot_actions: list[TestnetMonitorAction] = []
        self.every_epoch_actions: list[TestnetMonitorAction] = []
        self.once_actions: list[TestnetMonitorAction] = []

    def slot_to_epoch(self, slot_num: int) -> int:
        """Convert slot number to epoch number.

        @param slot_num: slot @return:
        """
        return slot_num // self.slots_per_epoch

    def epoch_to_slot(self, epoch_num: int) -> int:
        """Convert epoch number to slot number.

        @param epoch_num: epoch @return:
        """
        return epoch_num * self.slots_per_epoch

    def get_slot(self) -> int:
        """Get the current slot wrt to genesis time @return: slot numbuer."""
        return (int(time.time()) - self.consensus_genesis_time) // self.seconds_per_slot

    def get_epoch(self) -> int:
        """Get the current epoch wrt to genesis time @return:"""
        return self.get_slot() // self.slots_per_epoch

    def wait_for_slot(self, target_slot: int):
        """Wait until target slot.

        @param target_slot: slot to wait for @return:
        """
        t_delta: int = (target_slot - self.get_slot()) * self.seconds_per_slot
        while t_delta > 0:
            logging.debug(f"Waiting for slot {target_slot}")
            sleep_time = min(t_delta, 60)
            logging.debug(
                f"Waiting for target slot: {target_slot}, sleeping for {sleep_time} seconds"
            )
            time.sleep(sleep_time)
            t_delta = (target_slot - self.get_slot()) * self.seconds_per_slot

    def wait_for_epoch(self, target_epoch: int):
        """Wait until target epoch.

        @param target_epoch: epoch to wait for. @return:
        """
        self.wait_for_slot(self.epoch_to_slot(target_epoch))

    def add_action(self, action: TestnetMonitorAction):
        if action.interval == TestnetMonitorActionInterval.EVERY_SLOT:
            self.every_slot_actions.append(action)
        elif action.interval == TestnetMonitorActionInterval.EVERY_EPOCH:
            self.every_epoch_actions.append(action)
        elif action.interval == TestnetMonitorActionInterval.ONCE:
            self.once_actions.append(action)
        else:
            raise Exception("Invalid action interval")

    def run(self):
        """Optionally run the testnet monitor with actions."""
        if len(self.once_actions) > 0:
            logging.info("Performing one time actions.")
            for action in self.once_actions:
                action.perform_action()

        if len(self.every_slot_actions) == 0 and len(self.every_epoch_actions) == 0:
            return

        while True:
            goal_slot = self.get_slot() + 1
            self.wait_for_slot(goal_slot)
            logging.info(f"Expected slot: {goal_slot}")
            for action in self.every_slot_actions:
                action.perform_action()
            if goal_slot % self.slots_per_epoch == 0:
                for action in self.every_epoch_actions:
                    action.perform_action()
