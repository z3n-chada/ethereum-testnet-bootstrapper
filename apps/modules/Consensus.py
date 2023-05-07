"""
    Consensus related constants, enums, and abstractions.
"""

DEFINED_CONSENSUS_FORK_NAMES = ["phase0", "altair", "bellatrix", "capella", "deneb"]

class ConsensusFork(object):
    """
        Abstraction for a consensus fork.
    """
    def __init__(self, fork_name: str, fork_version: int, fork_epoch: int):
        if fork_name not in DEFINED_CONSENSUS_FORK_NAMES:
            raise ValueError(f"fork_name must be one of {DEFINED_CONSENSUS_FORK_NAMES}")
        self.name = fork_name
        self.version = fork_version
        self.epoch = fork_epoch

    def __str__(self):
        return f"{self.name}: 0x{self.version:02x} @ {self.epoch}"