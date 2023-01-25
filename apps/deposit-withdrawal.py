import random

from modules.ValidatorOperations import Ethdo, WithdrawalCredentialType
from modules.ETBConfig import ETBConfig


class WithdrawalDepositFuzzer(object):
    def __init__(self, etb_config: ETBConfig):
        self.etb_config = etb_config
        self.ethdo_interface = Ethdo(self.etb_config)

    def _get_random_premine_address(self):
        return random.choice(list(self.etb_config.get_premine_keypairs().keys()))

    def get_withdrawal_credential_type(self, ndx) -> WithdrawalCredentialType:
        addr_type, addr = self.ethdo_interface.get_validator_withdrawal_credentials(ndx)
        return addr_type

    def submit_bls_to_execution_change(self, ndx, address=None):
        if address is None:
            address = self._get_random_premine_address()
        try:
            self.ethdo_interface.send_bls_to_execution_change(ndx, address)
        except Exception as e:
            print(f"Got exception on bls change submission {e}")

    def submit_validator_exit(self, ndx):
        try:
            self.ethdo_interface.send_validator_exit(ndx)
        except Exception as e:
            print(f"Got exception on validator exit{e}")

    def submit_validator_deposit(self, ndx):
        pass

config = ETBConfig('configs/mainnet/geth-besu-capella.yaml')

fuzzer = WithdrawalDepositFuzzer(config)
# fuzzer.submit_bls_to_execution_change(8)
# print(fuzzer.get_withdrawal_credential_type(8))
fuzzer.submit_validator_exit(9)
fuzzer.submit_bls_to_execution_change(9)

