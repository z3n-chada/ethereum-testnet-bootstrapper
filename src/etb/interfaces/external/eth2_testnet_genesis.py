import logging
import pathlib
import subprocess
from typing import List, Union

from ruamel import yaml


class Eth2TestnetGenesis:
    """Eth2-testnet-genesis by protolambda."""

    def __init__(self, validator_mnemonic: str, num_validators: int):
        self.validator_mnemonic: str = validator_mnemonic
        self.num_validators: int = num_validators
        # where to dump the validators (this is temporary storage)
        self.validator_dump_yaml = pathlib.Path("/tmp/validators.yaml")

    def _cleanup(self):
        if self.validator_dump_yaml.exists():
            self.validator_dump_yaml.unlink()

    def _dump_validator_yaml(self):
        """Dumps the validator yaml file used later to generate the genesis.ssz
        file.

        Runs on __init__ @return:
        """
        self._cleanup()

        with open(self.validator_dump_yaml, "w", encoding="utf-8") as f:
            yaml.dump(
                [
                    {
                        "mnemonic": self.validator_mnemonic,
                        "count": self.num_validators,
                    }
                ],
                f,
            )

    def get_genesis_ssz(
        self,
        genesis_fork_name: str,
        config_in: pathlib.Path,
        genesis_ssz_out: pathlib.Path,
        preset_args: List[str],
    ) -> Union[bytes, Exception]:
        """Writes the genesis.ssz file.

        Usage:
            eth2-testnet-genesis {preset} --mnemonics {validators_yaml} --config {config_in} --state-output {genesis_ssz_out} ...
        @param genesis_fork_name: the genesis fork to use (bellatrix, capella, etc..)
        @param config_in: path to the config file.
        @param genesis_ssz_out: where to write the genesis.ssz files.
        @param preset_args: any additional args to pass to eth2-testnet-genesis (--preset-fork {preset})
        @return: genesis_ssz as bytes/stderr as Exception from eth2-testnet-genesis
        """
        # this is needed to generate the genesis.ssz file.
        self._dump_validator_yaml()

        cmd = [
            "eth2-testnet-genesis",
            genesis_fork_name,
            "--mnemonics",
            str(self.validator_dump_yaml),
            "--config",
            str(config_in),
            "--state-output",
            str(genesis_ssz_out),
        ]

        # add preset args.
        for arg in preset_args:
            cmd.append(arg)

        logging.debug(f"ConsensusGenesis: running eth2-testnet-genesis:\n{cmd}")
        out = subprocess.run(cmd, capture_output=True)
        if len(out.stderr) > 0:
            return Exception(out.stderr)

        with open(genesis_ssz_out, "rb") as f:
            data = f.read()

        return data
