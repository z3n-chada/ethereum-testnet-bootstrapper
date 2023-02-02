"""
    Classes that support validator operations such as deposits and withdrawals.
"""
import pathlib
import subprocess
import re
import shutil

from enum import Enum

from .ETBConfig import ETBConfig, ConsensusClient

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

    It also implements all the ethdo commands that *require* accounts

    """

    def __init__(self, etb_config: ETBConfig, wallet_path="/tmp/ethdo-wallet"):
        self.wallet_name = "ethdo-wallet"
        self.wallet_passphrase = "wallet-passphrase"
        self.wallet_path = wallet_path
        self.accounts = []
        self.account_passphrase = "account-passphrase"
        self.mnemonic = etb_config.get('validator-mnemonic')

        # remove an old wallet before using this one.
        if self._wallet_exists():
            self._remove_wallet()

        # create the wallet
        self._create_wallet()

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

    def account_from_ndx(self, ndx: int) -> str:
        """
        Keeping the account naming convention.
        :param ndx:
        :return:
        """
        return f'{self.wallet_name}/validator{ndx}'

    def _wallet_exists(self):
        return pathlib.Path(self.wallet_path).exists()

    def _remove_wallet(self):
        if self._wallet_exists():
            shutil.rmtree(self.wallet_path)

    def _create_wallet(self):
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
            self.account_from_ndx(ndx),
            '--passphrase',
            self.account_passphrase
        ]
        out = subprocess.run(cmd, capture_output=True)
        if len(out.stderr) > 0:
            raise Exception(f"Exception on account create {out.stderr}")

        self.accounts.append(ndx)

        return out.stdout



class Ethdo(object):
    def __init__(self, etb_config):
        self.config: ETBConfig = etb_config
        self.mnemonic = self.config.get('validator-mnemonic')
        self.wallet: EthdoWallet = EthdoWallet(etb_config)
        self._add_genesis_accounts()

    def _add_genesis_accounts(self):
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

    def generate_deposit_data(self, ndx, amount_ether=32, fork_version=None):
        '''
        Generates a raw tx for the deposit data.
        :param ndx:
        :return:
        '''
        if ndx not in self.wallet.accounts:
            self.wallet.add_account(ndx)
        amount_wei = amount_ether * (10 ** 18)
        if fork_version is None:
            forkversion = self.config.get('phase0-fork-version')
        else:
            forkversion = fork_version
        pub, priv = self.get_withdrawal_keys(ndx)
        cmd = [
            'ethdo',
            'validator',
            'depositdata',
            '--base-dir',
            self.wallet.wallet_path,
            '--wallet-passphrase',
            f'"{self.wallet.wallet_passphrase}"',
            '--passphrase',
            self.wallet.account_passphrase,
            "--validatoraccount",
            f"{self.wallet.account_from_ndx(ndx)}",
            '--forkversion',
            f"{forkversion}",
            '--depositvalue',
            f'{amount_wei}Wei',
            '--withdrawalpubkey',
            pub,
            '--launchpad',
            '--debug'
        ]

        out = subprocess.run(cmd, capture_output=True)
        if len(out.stderr) > 0:
            raise Exception(f"Failed to generate depositdata: {out.stderr}")

        return out.stdout.decode('utf-8')


# class ValidatorKeyStore(object):
#     def __init__(self, etb_config, validator_ndx: int):
#         self.index: int = validator_ndx
#         ethdo = Ethdo(etb_config)
#         self.validating_key_path = f"m/12381/3600/{str(self.index)}/0/0"
#         self.withdrawal_key_path = f"m/12381/3600/{str(self.index)}/0"
#         self.withdrawal_pub_key, self.withdrawal_priv_key = ethdo.get_withdrawal_keys()
#         self.validating_pub_key, self.validating_priv_key = ethdo.get_validating_keys()
