import logging
import pathlib
import random
import time
import argparse
import sys

from modules.Ethereal import Ethereal
from modules.BeaconAPI import ETBConsensusBeaconAPI, BeaconGetBlock
from modules.Ethdo import Ethdo, WithdrawalCredentialType
from modules.ETBConfig import ETBConfig, ExecutionClient




class WithdrawalSpammer(object):
    def __init__(self, etb_config: ETBConfig, max_actions_per_slot):
        self.etb_config = etb_config
        self.ethdo_interface = Ethdo(self.etb_config)
        self.max_actions_per_slot = max_actions_per_slot
        self.start_slot = int(self.etb_config.get('capella-fork-epoch')) * 32 - 12

        log_format = logging.Formatter("%(asctime)s: %(levelname)s: %(message)s")
        self.logger = logging.getLogger("withdrawal-spammer-log")
        self.stdout_handler = logging.StreamHandler(sys.stdout)
        self.stdout_handler.setLevel(logging.DEBUG)
        self.stdout_handler.setFormatter(log_format)
        self.logger.addHandler(self.stdout_handler)

    def _get_random_premine_address(self):
        return random.choice(list(self.etb_config.get_premine_keypairs().keys()))

    def get_withdrawal_credential_type(self, ndx) -> WithdrawalCredentialType:
        addr_type, addr = self.ethdo_interface.get_validator_withdrawal_credentials(ndx)
        return addr_type

    def submit_bls_to_execution_change(self, ndx, address=None):
        if address is None:
            address = self._get_random_premine_address()
        try:
            self.logger.info(f'doing submit_bls_to_execution_change({ndx})')
            self.ethdo_interface.send_bls_to_execution_change(ndx, address)
        except Exception as e:
            self.logger.warning(f"Got exception on bls change submission {e}")

    def submit_validator_exit(self, ndx):
        self.logger.info(f'doing submit_validator_exit({ndx})')
        try:
            self.ethdo_interface.send_validator_exit(ndx)
        except Exception as e:
            self.logger.warning(f"Got exception on validator exit{e}")

    def submit_validator_deposit(self, ndx, amount_ether=32):
        deposit_json = self.ethdo_interface.generate_deposit_data(ndx, amount_ether=amount_ether)
        depositdata_path = pathlib.Path('/tmp/deposit-data.json')
        ethereal = Ethereal(self.etb_config)
        try:
            with open(depositdata_path, 'w') as f:
                f.write(deposit_json)

            # choose a client to send the request to.
            eth1_client = self.etb_config.get_random_execution_client(client_filter='geth') # geth has personal
            eth1_connection = eth1_client.get_rpc_path()
            # unlock the account
            eth1_pub, eth1_priv = self.etb_config.get_random_eth1_key_pair()
            # etb_execution_rpc = ETBExecutionRPC(self.etb_config)
            # unlock_rpc = personal_unlock_account_RPC(address=eth1_pub, duration=0, passphrase=self.etb_config.get('eth1-passphrase'))
            # response = etb_execution_rpc.do_rpc_request(unlock_rpc,[eth1_client.name], all_clients=False)
            # print(response[eth1_client.name])
            out = ethereal.beacon_deposit(depositdata_path, eth1_connection, eth1_pub, eth1_priv)
            print(out)
        except Exception as e:
            print(f"submit_validator_deposit got exception: {e}", flush=True)
        finally:
            if depositdata_path.exists():
                depositdata_path.unlink()

    def do_action(self):
        options = [
            self.submit_bls_to_execution_change,
            self.submit_validator_exit,
            None
        ]

        action = random.choice(options)
        ndx_max = random.randint(0, 60)
        if action is not None:
            action(ndx_max)

    def on_slot(self):
        num_actions = random.randint(1, self.max_actions_per_slot)
        for x in range(num_actions):
            self.do_action()

    def get_curr_slot(self):
        client = self.etb_config.get_random_consensus_client()
        beacon_api_request = BeaconGetBlock('head')
        etb_beacon_api = ETBConsensusBeaconAPI(self.etb_config, timeout=5)
        responses = etb_beacon_api.do_api_request(beacon_api_request, client_nodes=[client.name], all_clients=False)
        response = list(responses.values())[0]
        return response.json()['data']['message']['slot']

    def wait_for_slot(self, goal):
        curr_slot = 0

        while curr_slot < goal:
            try:
                curr_slot = int(self.get_curr_slot())
                if goal - curr_slot > 10:
                    time.sleep(12 * 10)
                time.sleep(6)
            except:
                time.sleep(12)
                curr_slot = curr_slot + 1
            self.logger.debug(f'Waiting for slot: {goal} currently at {curr_slot}')

    def fuzz(self):
        self.wait_for_slot(self.start_slot)
        max_run_time = 12 * 30
        start_time = int(time.time())
        exit_time = start_time + max_run_time

        goal_slot = self.start_slot
        observed_slot = 0

        while True:
            # wait condition
            while observed_slot < goal_slot:
                try:
                    observed_slot = int(self.get_curr_slot())
                    time.sleep(3)
                # print(f'got observed slot: {observed_slot}', flush=True)
                except Exception as e:
                    # some unknown issue. just wait 12 seconds.
                    self.logger.warning(f'failed to get slot, using: {observed_slot}')
                    time.sleep(12)
            goal_slot = observed_slot + 1
            self.on_slot()
            self.stdout_handler.flush()
            if int(time.time()) > exit_time:
                return


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
        help="how many operations to do per slot."
    )

    args = parser.parse_args()

    while not pathlib.Path("/data/etb-config-file-ready").exists():
        print("waiting on etb-config file to be ready..", flush=True)
        time.sleep(1)

    etb_config = ETBConfig(args.config)
    fuzzer = WithdrawalSpammer(etb_config, args.max_operations_per_slot)
    fuzzer.fuzz()
