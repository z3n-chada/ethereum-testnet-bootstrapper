"""
    Some generic boilerplate code for modules and scripts.
"""
import logging
import pathlib
import subprocess
import sys
from .ETBConfig import ETBConfig
from ruamel import yaml


from .ETBConstants import ForkVersion, MinimalPreset


def create_logger(
    name: str, log_level: str, log_file_root="/source/data"
) -> logging.Logger:
    logging_levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "critical": logging.CRITICAL,
        "error": logging.ERROR,
        "warning": logging.WARNING,
    }
    if log_level.lower() not in logging_levels:
        log_level = logging.DEBUG
    else:
        log_level = logging_levels[log_level.lower()]
    log_format = logging.Formatter("%(asctime)s: %(levelname)s: %(message)s")
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(log_level)
    stdout_handler.setFormatter(log_format)
    logger.addHandler(stdout_handler)

    file_handler = logging.FileHandler(f"{log_file_root}/{name}.log")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    return logger


def write_checkpoint_file(path: str):
    """
    Write a checkpoint file.
    """
    with open(path, "w") as f:
        f.write("1")


"""
    Wrappers for various tools.
"""


class Eth2ValTools(object):
    def __init__(self, logger: logging.Logger = None):
        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger

    def generate_deposit_data(
        self, ndx: int, amount: int, fork_version: str, mnemonic: str
    ):
        """
        Generate a deposit data file for a validator.
        :param ndx: the validator index
        :param amount: amount of ether to deposit
        :param fork_version: fork version to use
        :param mnemonic: validator mnemonic
        :return:
        """

        self.logger.debug(
            f"Generating deposit for validator {ndx} with {amount} ether."
        )
        cmd = [
            "eth2-val-tools",
            "deposit-data",
            "--amount",
            str(amount),
            "--fork-version",
            str(fork_version),
            "--source-min",
            str(ndx),
            "--source-max",
            str(ndx + 1),
            "--validators-mnemonic",
            mnemonic,
            "--withdrawals-mnemonic",
            mnemonic,
        ]

        out = subprocess.run(cmd, capture_output=True)
        if len(out.stderr) > 0:
            raise Exception(f"Exception on deposit-data creation {out.stderr}")

        return out.stdout.decode("utf-8")

    def generate_keystores(
        self,
        out_path: str,
        min_ndx: int,
        max_ndx: int,
        mnemonic: str,
        prysm: bool = False,
        prysm_password: str = "testnet_password",
    ):
        """
        Generate keystores for a range of validators.
        :param out_path: output path for the keystores
        :param min_ndx: minimum validator index
        :param max_ndx: maximum validator index
        :param mnemonic: the mnemonic to use to generate the keystores
        :param prysm: if True, generate prysm keystores
        :param prysm_password: what password to use for prysm keystores
        :return:
        """

        self.logger.debug(
            f"Generating keystores for validators {min_ndx} to {max_ndx}."
        )
        cmd = [
            "eth2-val-tools",
            "keystores",
            "--source-min",
            str(min_ndx),
            "--source-max",
            str(max_ndx),
            "--source-mnemonic",
            mnemonic,
            "--out-loc",
            out_path,
        ]

        if prysm:
            cmd.append("--prysm-pass")
            cmd.append(prysm_password)

        out = subprocess.run(cmd, capture_output=True)
        if len(out.stderr) > 0:
            raise Exception(f"Exception on keystores creation {out.stderr}")

        return out.stdout.decode("utf-8")


class Ethereal(object):
    def __init__(self, logger: logging.Logger = None):

        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger

    def beacon_deposit(
        self,
        client_jsonrpc_path: str,
        premine_key_pair,
        deposit_data: str,
        chain_id: int,
        deposit_contract: str,
        wait=False,
    ):
        """
        Send a beacon deposit to the beacon chain.
        :param client_jsonrpc_path: str representing the path to the client's jsonrpc endpoint
        :param premine_key_pair: KeyPair object representing the premine keypair
        :param deposit_data: str representing the deposit data
        :param chain_id: int representing the chain id
        :param deposit_contract: str representing the deposit contract address
        :param wait: bool representing whether to wait for the transaction to be mined
        :return:
        """
        self.logger.info("Sending the beacon deposit")
        self.logger.debug(f"deposit-data: {deposit_data}")
        with open("/tmp/deposit_data", "w") as f:
            f.write(deposit_data)
        cmd = [
            "ethereal",
            "beacon",
            "deposit",
            "--allow-duplicate-deposit",
            "--allow-excessive-deposit",
            "--allow-new-data",
            "--allow-old-data",
            "--allow-unknown-contract",
            "--connection",
            client_jsonrpc_path,
            "--data",
            "/tmp/deposit_data",
            "--chainid",
            str(chain_id),
            "--address",
            deposit_contract,
            "--from",
            premine_key_pair.public_key,
            "--privatekey",
            premine_key_pair.private_key,
        ]
        if wait:
            cmd.append("--wait")
        out = subprocess.run(cmd, capture_output=True)
        if len(out.stderr) > 0:
            raise Exception(f"Exception on account create {out.stderr}")

        return out.stdout


class Eth2TestnetGenesis(object):
    def __init__(self, etb_config: ETBConfig, logger: logging.Logger = None):
        self.etb_config: ETBConfig = etb_config
        self.validator_dump_yaml = pathlib.Path("/tmp/validators.yaml")
        if logger is None:
            self.logger = logging.getLogger()
        else:
            self.logger = logger

    def _cleanup(self):
        if self.validator_dump_yaml.exists():
            self.validator_dump_yaml.unlink()

    def _dump_validator_yaml(self):
        self._cleanup()

        mnemonic = self.etb_config.accounts.get("validator-mnemonic")
        num_deposits = self.etb_config.config_params.get(
            "min-genesis-active-validator-count"
        )

        with open(self.validator_dump_yaml, "w") as f:
            yaml.dump(
                [
                    {
                        "mnemonic": mnemonic,
                        "count": num_deposits,
                    }
                ],
                f,
            )

    def write_genesis_ssz(self):
        # this is needed to generate the genesis.ssz file.
        self._dump_validator_yaml()
        genesis_fork_version: ForkVersion = self.etb_config.get_genesis_fork_upgrade()
        consensus_config = self.etb_config.files.get("consensus-config-file")
        state_out = self.etb_config.files.get("consensus-genesis-file")

        if self.etb_config.preset_base == MinimalPreset:
            preset_base_str = "minimal"
        else:
            preset_base_str = "mainnet"

        cmd = [
            "eth2-testnet-genesis",
            f"{genesis_fork_version.name.lower()}",
            "--mnemonics",
            "/tmp/validators.yaml",
            "--config",
            consensus_config,
            "--state-output",
            state_out,
        ]

        # add preset-base args
        if genesis_fork_version >= ForkVersion.Phase0:
            cmd.append("--preset-phase0")
            cmd.append(preset_base_str)

        if genesis_fork_version >= ForkVersion.Altair:
            cmd.append("--preset-altair")
            cmd.append(preset_base_str)

        if genesis_fork_version >= ForkVersion.Bellatrix:
            cmd.append("--preset-bellatrix")
            cmd.append(preset_base_str)
            cmd.append("--eth1-config")
            cmd.append(self.etb_config.files.get("geth-genesis-file"))

        if genesis_fork_version >= ForkVersion.Capella:
            cmd.append("--preset-capella")
            cmd.append(preset_base_str)

        self.logger.debug(f"ConsensusGenesis: running eth2-testnet-genesis:\n{cmd}")

        out = subprocess.run(cmd, capture_output=True)
        if len(out.stderr) > 0:
            raise Exception(f"Exception consensus genesis ssz: {out.stderr}")

        with open(state_out, "rb") as f:
            ssz = f.read()

        return ssz


class Ethdo(object):
    """
    Wrapper for the ethdo tool.
    Supports the following commands:
    - validator_exit
    - submit_bls_to_execution_change
    """

    def __init__(
        self, mnemonic: str, withdrawal_address: str, logger: logging.Logger = None
    ):
        self.mnemonic = mnemonic
        self.withdrawal_address = withdrawal_address
        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger

    def submit_validator_exit(self, connection: str, ndx: int):
        """
        Send a validator exit to the beacon node.
        :param connection: string representation of the beacon node connection.
        :param ndx: the validator index to exit.
        :return: stdout of the ethdo command.
        """
        cmd = [
            "ethdo",
            "validator",
            "exit",
            "--mnemonic",
            self.mnemonic,
            "--validator",
            str(ndx),
            "--connection",
            connection,
        ]

        out = subprocess.run(cmd, capture_output=True)

        if len(out.stderr) > 0:
            raise Exception(f"Exception on validator exit {out.stderr}")

        return out.stdout.decode("utf-8")

    def submit_bls_to_execution_change(
        self, connection: str, ndx: int, withdrawal_address: str = None
    ) -> str:
        """
        Send a bls to execution change to the beacon node.
        :param connection: string representation of the beacon node connection.
        :param ndx: the validator index to change.
        :param withdrawal_address: optional withdrawal address to change to.
        :return: stdout of the ethdo command.
        """

        if withdrawal_address is None:
            withdrawal_addr = self.withdrawal_address
        else:
            withdrawal_addr = withdrawal_address

        cmd = [
            "ethdo",
            "validator",
            "credentials",
            "set",
            "--mnemonic",
            self.mnemonic,
            "--validator",
            str(ndx),
            "--connection",
            connection,
            "--withdrawal-address",
            withdrawal_addr,
        ]

        out = subprocess.run(cmd, capture_output=True)
        if len(out.stderr) > 0:
            raise Exception(f"Exception on bls exchange {out.stderr}")

        return out.stdout.decode("utf-8")
