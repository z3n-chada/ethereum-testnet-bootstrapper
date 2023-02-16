import logging
import os
import pathlib
import random
import time
import argparse

from modules.TestnetMonitor import TestnetMonitor
from modules.ETBConfig import ETBConfig, ClientInstance
from modules.ETBUtils import Ethereal, create_logger, Eth2ValTools, Ethdo


class ValidatorOperationFuzzer(object):
    """
    Spams various operations on the validator set.

    Until Capella this will perform deposits.
    After Capella this will perform BLSToExecution/Exit messages.
    """

    def __init__(
        self,
        etb_config: ETBConfig,
        logger: logging.Logger = None,
        max_actions_per_slot=5,
        max_deposits: int = -1,  # -1 means we calculate on the etb_config
        start_slot: int = -1,  # defaults to first epoch.
        end_slot: int = -1,  # defaults to 4 epochs past capella fork.
        validator_operations_start_slot: int = -1,  # defaults to 1 epoch before capella fork.
        only_valid_deposits: bool = False,  # whether to send valid or invalid deposits.
    ):
        self.etb_config = etb_config

        if logger is None:
            self.logger = logging.getLogger()
        else:
            self.logger = logger

        # default mnemonic path for validator operations
        self.mnemonic = self.etb_config.accounts.get("validator-mnemonic")
        # default withdrawal address for validator operations
        self.withdrawal_address = self.etb_config.accounts.get(
            "eth1-withdrawal-address"
        )

        self.ethereal = Ethereal(self.logger)
        self.eth2valtools = Eth2ValTools(self.logger)
        self.ethdo = Ethdo(self.mnemonic, self.withdrawal_address, self.logger)
        self.testnet_monitor = TestnetMonitor(self.etb_config, self.logger)

        self.deposit_data_path = "/tmp/deposit_data.json"
        self.max_actions_per_slot = max_actions_per_slot

        if max_deposits == -1:
            self.max_deposits = (
                self.etb_config.get_number_of_unaccounted_validator_deposits()
            )
        else:
            self.max_deposits = max_deposits

        self.curr_deposits = 0
        self.max_ndx = (
            self.etb_config.config_params.get("min-genesis-active-validator-count")
            + self.max_deposits
        )

        self.only_valid_deposits = only_valid_deposits
        if self.only_valid_deposits:
            deposit_ndx_start = self.etb_config.config_params.get(
                "min-genesis-active-validator-count"
            )
            deposit_ndx_end = (
                deposit_ndx_start
                + self.etb_config.get_number_of_unaccounted_validator_deposits()
            )
            self.valid_deposit_ndxs = [
                x for x in range(deposit_ndx_start + 1, deposit_ndx_end)
            ]
        # compute defaults if necessary.
        if start_slot == -1:
            self.start_slot = self.etb_config.epoch_to_slot(1)
        else:
            self.start_slot = start_slot

        if end_slot == -1:
            self.end_slot = self.etb_config.epoch_to_slot(
                self.etb_config.config_params.get("capella-fork-epoch") + 4
            )
        else:
            self.end_slot = end_slot

        if validator_operations_start_slot == -1:
            self.validator_operations_start_slot = self.etb_config.epoch_to_slot(
                self.etb_config.config_params.get("capella-fork-epoch") - 1
            )
        else:
            self.validator_operations_start_slot = validator_operations_start_slot

        self.logger.debug(f"ValidatorOperationFuzzer configured with:")
        self.logger.debug(f"start_slot: {self.start_slot}")
        self.logger.debug(f"end_slot: {self.end_slot}")
        self.logger.debug(
            f"validator_operations_start_slot: {self.validator_operations_start_slot}"
        )
        self.logger.debug(f"max_actions_per_slot: {self.max_actions_per_slot}")
        self.logger.debug(f"max_deposits: {self.max_deposits}")
        self.logger.debug(f"only_valid_deposits: {self.only_valid_deposits}")
        if self.only_valid_deposits:
            self.logger.debug(f"valid_deposit_ndxs: {self.valid_deposit_ndxs}")

    def send_deposit_data(self, client: ClientInstance, ndx: int) -> None:

        fork_version = (
            f"0x{self.etb_config.config_params.get('phase0-fork-version'):08x}"
        )
        # TODO fix getter.
        chain_id = self.etb_config.config_params.get("chain-id")
        deposit_contract = self.etb_config.config_params.get("deposit-contract-address")
        jsonrpc_path = client.get_full_execution_http_jsonrpc_path()
        pkp = random.choice(self.etb_config.get_premine_keypairs())
        if self.only_valid_deposits:
            if len(self.valid_deposit_ndxs) == 0:
                self.logger.info("No more valid deposits to send.")
                return
            validator_ndx = self.valid_deposit_ndxs.pop(0)
            amount: int = 32000000000
        else:
            # 2 to 64 ETH and only new validators.
            validator_ndx = random.randint(
                self.etb_config.config_params.get("min-genesis-active-validator-count"),
                self.max_ndx,
            )
            amount: int = random.randint(2_000_000_000, 64_000_000_000)
        # generate
        deposit_data = self.eth2valtools.generate_deposit_data(
            validator_ndx, amount, fork_version, self.mnemonic
        )
        # send
        self.ethereal.beacon_deposit(
            jsonrpc_path, pkp, deposit_data, chain_id, deposit_contract
        )

    def _send_bls_to_execution_change(self, client: ClientInstance, ndx: int) -> None:
        self.ethdo.submit_bls_to_execution_change(
            client.get_full_beacon_api_path(), ndx
        )

    def _send_validator_exit(self, client: ClientInstance, ndx: int) -> None:
        self.ethdo.submit_validator_exit(client.get_full_beacon_api_path(), ndx)

    def do_actions(self):
        actions = [
            self._send_validator_exit,
            self._send_bls_to_execution_change,
            self.send_deposit_data,
            None,
        ]
        # which actions are only allowed after the validator operations start slot.
        validator_actions = [
            self.ethdo.submit_validator_exit,
            self.ethdo.submit_bls_to_execution_change,
        ]

        for x in range(random.randint(0, self.max_actions_per_slot)):
            action = random.choice(actions)
            # the ndx is patched in the send_deposit_data function.
            ndx = random.randint(0, self.max_ndx)

            if action is not None:
                # wait for root state
                slot = self.testnet_monitor.get_slot()
                if (
                    slot < self.validator_operations_start_slot
                    and action in validator_actions
                ):
                    self.logger.info(
                        f"current slot: {slot} postponing validator operation until: {self.validator_operations_start_slot}"
                    )
                else:
                    client: ClientInstance = random.choice(
                        self.etb_config.get_client_instances()
                    )
                    self.logger.info(
                        f"submitting action: {action.__name__} to client: {client.name}"
                    )
                    try:
                        action(client, ndx)
                    except Exception as e:
                        # this could be expected based on down stream randomness.
                        print(
                            f"while trying to fuzz {action.__name__} we got exception: {e}"
                        )

    def fuzz(self):
        # wait until start
        self.logger.info(f"Waiting until slot: {self.start_slot} to fuzz.")
        self.testnet_monitor.wait_for_slot(self.start_slot)
        curr_slot = self.start_slot

        while self.testnet_monitor.get_slot() < self.end_slot:
            self.do_actions()
            self.testnet_monitor.wait_for_slot(curr_slot + 1)
            curr_slot += 1


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        dest="config",
        required=True,
        help="path to config file to consume for experiment",
    )

    parser.add_argument(
        "--max-operations-per-slot",
        dest="max_operations_per_slot",
        type=int,
        default=5,
        help="how many operations to do per slot.",
    )

    parser.add_argument(
        "--start-slot",
        dest="start_slot",
        type=int,
        default=-1,
        help="when to start spamming messages. Defaults to first epoch.",
    )

    parser.add_argument(
        "--end-slot",
        dest="end_slot",
        type=int,
        default=-1,
        help="when to end spamming messages. Defaults to 4 epochs after capella.",
    )

    parser.add_argument(
        "--validator-operations-start-slot",
        dest="validator_operations_start_slot",
        type=int,
        default=-1,
        help="when to start sending capella validator operations. Defaults to 1 epoch before capella.",
    )

    parser.add_argument(
        "--max-deposits",
        dest="max_deposits",
        type=int,
        default=-1,
        help="what the max deposit target is, defaults to the difference of min-genesis-validator-count and how many "
        "validators we have.",
    )

    parser.add_argument(
        "--only-valid-deposits",
        dest="only_valid_deposits",
        action="store_true",
        default=False,
        help="if true don't send invalid or duplicate deposits.",
    )

    parser.add_argument(
        "--only-valid-deposits",
        dest="only_valid_deposits",
        action="store_true",
        default=False,
        help="if true don't send invalid or duplicate deposits.",
    )

    parser.add_argument(
        "--seed",
        dest="seed",
        default=None,
        help="seed to use for random number generation.",
    )

    args = parser.parse_args()

    while not pathlib.Path("/data/etb-config-file-ready").exists():
        print("waiting on etb-config file to be ready..", flush=True)
        time.sleep(1)

    _logger = create_logger("ValidatorOperationFuzzer", "debug")
    _etb_config = ETBConfig(args.config, _logger)

    if args.seed is not None:
        _logger.info(f"Using user supplied random seed: {args.seed}")
        random.seed(args.seed)

    else:
        rand = os.urandom(10)
        seed = int.from_bytes(rand, "big")
        _logger.info(f"setting random seed to: {seed}")
        random.seed(seed)

    fuzzer: ValidatorOperationFuzzer = ValidatorOperationFuzzer(
        _etb_config,
        _logger,
        start_slot=args.start_slot,
        end_slot=args.end_slot,
        max_actions_per_slot=args.max_operations_per_slot,
        validator_operations_start_slot=args.validator_operations_start_slot,
        max_deposits=args.max_deposits,
        only_valid_deposits=args.only_valid_deposits,
    )
    fuzzer.fuzz()
