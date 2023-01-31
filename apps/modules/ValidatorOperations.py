"""
    Classes that support validator operations such as deposits and withdrawals.
"""
import json
import pathlib
import random
import shutil
import subprocess
import re
from enum import Enum

from .ETBConfig import ETBConfig, ConsensusClient
from .BeaconAPI import GetValidators, ETBConsensusBeaconAPI, GetFork, GetGenesis

hex_regex = re.compile(r'0x[0-9a-fA-F]+')
account_name_regex = re.compile(r'[0-9]+')


class WithdrawalCredentialType(Enum):
    BLS = 0
    Execution = 1


class EthdoWallet(object):
    """
    Ethdo uses wallets for some of its features. So this object
    keeps track of the data so we don't have to generate them
    repeatedly.

    It also implements all of the ethdo commands that *require* accounts

    """

    def __init__(self, etb_config: ETBConfig, wallet_path="/tmp/ethdo-wallet"):
        self.wallet_name = "ethdo-wallet"
        self.wallet_passphrase = "wallet-passphrase"
        self.wallet_path = wallet_path
        self.accounts = []
        self.account_passphrase = "account-passphrase"
        self.mnemonic = etb_config.get('validator-mnemonic')

        if not self._wallet_exists():
            self.create_wallet()
        else:
            self._get_accounts_from_wallet_dir()

    def _get_accounts_from_wallet_dir(self):
        cmd = [
            'ethdo',
            'wallet',
            'accounts',
            '--wallet',
            self.wallet_name,
            '--base-dir',
            self.wallet_path,
            '--wallet-passphrase',
            f'"{self.wallet_passphrase}"',
        ]
        out = subprocess.run(cmd, capture_output=True)
        if len(out.stderr) > 0:
            raise Exception(f"Exception on account list {out.stderr}")
        accounts = (out.stdout.decode('utf-8').split('\n'))
        accounts.remove('')

        for account_name in accounts:
            ndx = account_name_regex.search(account_name).group()
            self.accounts.append(int(ndx, 10))

    def _wallet_exists(self):
        return pathlib.Path(self.wallet_path).exists()

    def _remove_wallet(self):
        if self._wallet_exists():
            shutil.rmtree(self.wallet_path)

    def create_wallet(self):
        """
        remove the old wallet and create a new one.

        """

        cmd = [
            'ethdo',
            'wallet',
            'create',
            '--type',
            'hd',
            '--wallet',
            self.wallet_name,
            '--base-dir',
            self.wallet_path,
            '--mnemonic',
            self.mnemonic,
            '--wallet-passphrase',
            f'"{self.wallet_passphrase}"',
            '--allow-weak-passphrases',
        ]
        out = subprocess.run(cmd, capture_output=True)
        if len(out.stderr) > 0:
            raise Exception(f"Exception on wallet create {out.stderr}")

        return out.stdout

    def add_account(self, ndx):
        """
        Add an account if it does not exist
        :param ndx:
        :return:
        """
        if ndx in self.accounts:
            return
        # self._get_accounts_from_wallet_dir()
        cmd = [
            'ethdo',
            'account',
            'create',
            '--base-dir',
            self.wallet_path,
            '--wallet-passphrase',
            f'"{self.wallet_passphrase}"',
            '--path',
            f"m/12381/3600/{ndx}/0/0",
            '--account',
            f'{self.wallet_name}/validator{ndx}',
            '--passphrase',
            self.account_passphrase
        ]
        out = subprocess.run(cmd, capture_output=True)
        if len(out.stderr) > 0:
            raise Exception(f"Exception on account create {out.stderr}")

        self.accounts.append(ndx)

        return out.stdout

    def refresh(self):
        self._remove_wallet()
        self.create_wallet()


class Ethdo(object):
    def __init__(self, etb_config, offline_data_path='/tmp/offline-data.json', refresh=True):
        self.config: ETBConfig = etb_config
        self.mnemonic = self.config.get('validator-mnemonic')
        self.offline_data_path = pathlib.Path(offline_data_path)
        self.wallet: EthdoWallet = EthdoWallet(etb_config)
        self.add_genesis_accounts()

        if refresh or not self.offline_data_path.exists():
            self._prepare_offline_data()

    def _prepare_offline_data(self):
        default_output_file = pathlib.Path('offline-preparation.json')
        cmd = [
            'ethdo',
            'validator',
            'exit',
            '--mnemonic',
            f'\"{self.mnemonic}\"',
            '--prepare-offline',
            '--connection',
            f'{self.config.get_random_consensus_client().get_beacon_api_path()}'
        ]
        x = subprocess.run(cmd, capture_output=True)
        if len(x.stderr) > 0:
            raise Exception(f"Failed to prepare offline data: {x.stderr}")

        with open(default_output_file, 'r') as f:
            offline_prep_data = json.load(f)

        default_output_file.unlink()

        if self.offline_data_path.exists():
            self.offline_data_path.unlink()

        with open(self.offline_data_path, 'w') as f:
            json.dump(offline_prep_data, f)

    def add_genesis_accounts(self):
        """
        Adds all the preseeded genesis accounts to ethdo with type0 credentials
        :return:
        """
        for x in range(self.config.get('min-genesis-active-validator-count')):
            self.wallet.add_account(x)


    def get_withdrawal_keys(self, ndx) -> tuple[str, str]:
        path = f"m/12381/3600/{ndx}/0"
        cmd = [
            "ethdo",
            "account",
            "derive",
            "--mnemonic",
            self.mnemonic,
            "--path",
            path
        ]
        out = subprocess.run(cmd, capture_output=True)
        pubkey = hex_regex.search(str(out.stdout)).group()
        cmd.append('--show-private-key')
        out = subprocess.run(cmd, capture_output=True)
        privkey = hex_regex.search(str(out.stdout)).group()
        return pubkey, privkey

    def send_bls_to_execution_change(self, ndx, address, mnemonic=None, client: ConsensusClient = None):
        if ndx not in self.wallet.accounts:
            self.wallet.add_account(ndx)

        if mnemonic is None:
            mnemonic = self.mnemonic

        if client is None:
            connection = self.config.get_random_consensus_client().get_beacon_api_path()
        else:
            connection = client.get_beacon_api_path()

        cmd = [
            'ethdo',
            'validator',
            'credentials',
            'set',
            '--mnemonic',
            mnemonic,
            '--validator',
            str(ndx),
            '--connection',
            connection,
            '--withdrawal-address',
            address,
        ]

        out = subprocess.run(cmd, capture_output=True)
        if len(out.stderr) > 0:
            raise Exception(f"Exception on bls exchange {out.stderr}")

    def send_validator_exit(self, ndx, mnemonic=None, client: ConsensusClient = None):
        if ndx not in self.wallet.accounts:
            self.wallet.add_account(ndx)

        if mnemonic is None:
            mnemonic = self.mnemonic

        if client is None:
            connection = self.config.get_random_consensus_client().get_beacon_api_path()
        else:
            connection = client.get_beacon_api_path()

        cmd = [
            'ethdo',
            'validator',
            'exit',
            'set',
            '--mnemonic',
            mnemonic,
            '--validator',
            str(ndx),
            '--connection',
            connection,
        ]

        out = subprocess.run(cmd, capture_output=True)
        if len(out.stderr) > 0:
            raise Exception(f"Exception on validator exit {out.stderr}")

        return out.stdout.decode('utf-8')

    def get_validating_keys(self, ndx) -> tuple[str, str]:
        path = f"m/12381/3600/{ndx}/0/0"
        cmd = [
            "ethdo",
            "account",
            "derive",
            "--mnemonic",
            self.mnemonic,
            "--path",
            path
        ]
        out = subprocess.run(cmd, capture_output=True)
        pubkey = hex_regex.search(str(out.stdout)).group()
        cmd.append('--show-private-key')
        out = subprocess.run(cmd, capture_output=True)
        privkey = hex_regex.search(str(out.stdout)).group()
        return pubkey, privkey

    def get_validator_withdrawal_credentials(self, ndx: int, client: ConsensusClient = None) -> tuple[
        WithdrawalCredentialType, str]:
        if client is None:
            client = self.config.get_random_consensus_client()

        rpc_path = client.get_beacon_api_path()
        cmd = [
            'ethdo',
            'validator',
            'credentials',
            'get',
            '--mnemonic',
            self.mnemonic,
            '--validator',
            str(ndx),
            '--connection',
            rpc_path
        ]
        out = subprocess.run(cmd, capture_output=True)
        if len(out.stderr) > 0:
            raise Exception(f"Failed to get withdrawal credentials: {out.stderr}")

        address_type, address = out.stdout.decode('utf-8').split(':')
        if "BLS credentials" in address_type:
            addr = WithdrawalCredentialType.BLS
        else:
            addr = WithdrawalCredentialType.Execution

        return addr, hex_regex.search(address).group()

    def get_block_info(self, block_num):
        connection = self.config.get_random_consensus_client().get_beacon_api_path()
        cmd = [
            'ethdo',
            'block',
            'info',
            '--blockid',
            f'{block_num}',
            '--connection',
            connection,
        ]
        out = subprocess.run(cmd, capture_output=True)
        if len(out.stderr) > 0:
            raise Exception(f"Failed to get block info: {out.stderr}")

        return out.stdout.decode('utf-8')

class ValidatorKeyStore(object):
    def __init__(self, etb_config, validator_ndx: int):
        self.index: int = validator_ndx
        ethdo = Ethdo(etb_config)
        self.validating_key_path = f"m/12381/3600/{str(self.index)}/0/0"
        self.withdrawal_key_path = f"m/12381/3600/{str(self.index)}/0"
        self.withdrawal_pub_key, self.withdrawal_priv_key = ethdo.get_withdrawal_keys()
        self.validating_pub_key, self.validating_priv_key = ethdo.get_validating_keys()
