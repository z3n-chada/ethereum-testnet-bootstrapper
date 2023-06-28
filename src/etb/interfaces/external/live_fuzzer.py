"""
LiveFuzzer interface
livefuzzer: github.com/mariusvanderwijden/tx-fuzz
"""
import logging
import pathlib
import subprocess


class LiveFuzzer:
    def __init__(
        self, binary_path: pathlib.Path = pathlib.Path("/usr/local/bin/livefuzzer")
    ):
        self.binary_path = binary_path

    def start_fuzzer(self, rpc_path: str, fuzz_mode: str, private_key: str):
        """Start the livefuzzer binary with the given parameters.

        @param rpc_path: path to the livefuzzer binary @param fuzz_mode:
        the mode to use @param private_keys: list of pkeys to use for
        signing @return:
        """
        cmd = [
            str(self.binary_path),
            fuzz_mode,
            "--rpc",
            rpc_path,
            "--sk",
            private_key,
        ]

        logging.debug(f"Starting livefuzzer with the following command: {cmd}")
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise Exception(e)
