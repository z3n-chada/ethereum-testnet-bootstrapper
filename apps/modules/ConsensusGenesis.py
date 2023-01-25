"""
    Contains all of the neccessary information and functionality to write the
    consensus config.yaml and genesis.ssz.
"""
import logging
import subprocess
from collections import OrderedDict

from ruamel import yaml

from .ETBConfig import ETBConfig, ForkVersion

logger = logging.getLogger("bootstrapper_log")


class ConsensusGenesisWriter(object):
    def __init__(self, etb_config):
        self.etb_config : ETBConfig = etb_config

        self.minimal_defaults = {
            "max-committees-per-slot": 4,
            "target-committee-size": 4,
            "shuffle-round-count": 10,
            "eth1-follow-distance": 16,
            "seconds-per-slot": 12,
            "slots-per-epoch": 8,
            "epochs-per-eth1-voting-period": 4,
            "slots-per-historical-root": 64,
            "shard-committee-period": 64,
            "epochs-per-historical-vector": 64,
            "epochs-per-slashings-vector": 64,
            "inactivity-penalty-quotient": 33554432,
            "min-slashing-penalty-quotient": 64,
            "proportional-slashing-multiplier": 2,
            "churn-limit-quotient": 32,
        }

        self.mainnet_defaults = {
            "max-committees-per-slot": 64,
            "target-committee-size": 128,
            "shuffle-round-count": 90,
            "eth1-follow-distance": 2048,
            "seconds-per-slot": 12,
            "slots-per-epoch": 32,
            "epochs-per-eth1-voting-period": 64,
            "slots-per-historical-root": 8192,
            "shard-committee-period": 256,
            "epochs-per-historical-vector": 65536,
            "epochs-per-slashings-vector": 8192,
            "inactivity-penalty-quotient": 67108864,
            "min-slashing-penalty-quotient": 128,
            "proportional-slashing-multiplier": 2,
            "churn-limit-quotient": 65536,
        }

        self.potential_overrides = [
            "eth1-follow-distance",
            "min-genesis-active-validator-count",
        ]

    def create_consensus_genesis(self):
        """
        Create the consensus genesis.ssz file with eth2-testnet-genesis.
        currently we only use post-merge genesis with no withdrawal.
        """
        mnemonic = self.etb_config.get("validator-mnemonic")
        config = self.etb_config.get("consensus-config-file")
        state_out = self.etb_config.get("consensus-genesis-file")
        num_deposits = self.etb_config.get("min-genesis-active-validator-count")
        eth1_config = self.etb_config.get("geth-genesis-file")

        logger.debug("Creating genesis ssz using:")
        logger.debug(f"mnemonic: {mnemonic}")
        logger.debug(f"num_deposits {num_deposits}")
        logger.debug(f"config {config}")
        logger.debug(f"eth1-config {eth1_config}")
        logger.debug(f"ssz path: {state_out}")

        genesis_fork_cmd_map = {
            ForkVersion.Phase0 : "phase0",
            ForkVersion.Altair : "altair",
            ForkVersion.Bellatrix : "merge",
            ForkVersion.Capella : "merge",
        }

        fork_version: ForkVersion = self.etb_config.get_genesis_fork()

        with open("/tmp/validators.yaml", "w") as f:
            yaml.dump(
                [
                    {
                        "mnemonic": mnemonic,
                        "count": num_deposits,
                    }
                ],
                f,
            )

        cmd = [
            "eth2-testnet-genesis",
            f"{genesis_fork_cmd_map[fork_version]}",
            "--mnemonics",
            "/tmp/validators.yaml",
            "--config",
            config,
            "--state-output",
            state_out,
        ]
        if fork_version >= ForkVersion.Bellatrix:
            cmd.append("--eth1-config")
            cmd.append(eth1_config)
            #TODO
            # cmd.append('--eth1-withdrawal-address')
            # cmd.append()
        logger.debug(f"ConsensusGenesis: running eth2-testnet-genesis:\n{cmd}")
        subprocess.run(cmd, capture_output=True)

        with open(state_out, "rb") as f:
            ssz = f.read()

        return ssz

mainnet_config_defaults = {
    # time
    'SECONDS_PER_SLOT': 12,
    'SECONDS_PER_ETH1_BLOCK': 14,
    'MIN_VALIDATOR_WITHDRAWABILITY_DELAY': 256,
    'SHARD_COMMITTEE_PERIOD': 256,
    'ETH1_FOLLOW_DISTANCE': 2048,
    # validator cycle
    'EJECTION_BALANCE': 16_000_000_000,
    'MIN_PER_EPOCH_CHURN_LIMIT': 4,
    'CHURN_LIMIT_QUOTIENT': 65_536,
    # altair inactivity penalties
    'INACTIVITY_SCORE_BIAS': 4,
    'INACTIVITY_SCORE_RECOVERY_RATE': 16,
    # updated fork choice params
    'PROPOSER_SCORE_BOOST': 40,
    # bellatrix transition settings
    'TERMINAL_TOTAL_DIFFICULTY': 58750000000000000000000,
    'TERMINAL_BLOCK_HASH': "0x0000000000000000000000000000000000000000000000000000000000000000",
    'TERMINAL_BLOCK_HASH_ACTIVATION_EPOCH': 18446744073709551615,
    # misc
    'MAX_COMMITTEES_PER_SLOT': 64,
}


class ConsensusConfigurationWriter(object):
    def __init__(self, etb_config):
        self.etb_config: ETBConfig = etb_config

    def get_genesis_config_values(self) -> OrderedDict:
        config_entries = OrderedDict()
        config_entries['MIN_GENESIS_ACTIVE_VALIDATOR_COUNT'] = self.etb_config.get(
            'min-genesis-active-validator-count')
        config_entries['MIN_GENESIS_TIME'] = self.etb_config.get('bootstrap-genesis')
        config_entries['GENESIS_DELAY'] = self.etb_config.get('consensus-genesis-delay')
        config_entries['GENESIS_FORK_VERSION'] = f'0x{self.etb_config.get("phase0-fork-version"):08x}'
        return config_entries

    def get_forking_config_values(self) -> OrderedDict:
        config_entries = OrderedDict()
        config_entries['ALTAIR_FORK_VERSION'] = f'0x{self.etb_config.get("altair-fork-version"):08x}'
        config_entries['ALTAIR_FORK_EPOCH'] = self.etb_config.get('altair-fork-epoch')
        config_entries['BELLATRIX_FORK_VERSION'] = f'0x{self.etb_config.get("bellatrix-fork-version"):08x}'
        config_entries['BELLATRIX_FORK_EPOCH'] = self.etb_config.get('bellatrix-fork-epoch')
        config_entries['CAPELLA_FORK_VERSION'] = f'0x{self.etb_config.get("capella-fork-version"):08x}'
        config_entries['CAPELLA_FORK_EPOCH'] = self.etb_config.get('capella-fork-epoch')
        config_entries['SHARDING_FORK_VERSION'] = f'0x{self.etb_config.get("sharding-fork-version"):08x}'
        config_entries['SHARDING_FORK_EPOCH'] = self.etb_config.get('sharding-fork-epoch')
        config_entries['EIP4844_FORK_VERSION'] = f'0x{self.etb_config.get("eip4844-fork-version"):08x}'
        config_entries['EIP4844_FORK_EPOCH'] = self.etb_config.get('eip4844-fork-epoch')
        return config_entries

    def get_deposit_config_values(self) -> OrderedDict:
        config_entries = OrderedDict()
        config_entries['DEPOSIT_CHAIN_ID'] = self.etb_config.get('chain-id')
        config_entries['DEPOSIT_NETWORK_ID'] = self.etb_config.get('network-id')
        config_entries['DEPOSIT_CONTRACT_ADDRESS'] = self.etb_config.get('deposit-contract-address')
        return config_entries

    def get_time_parameters_config_values(self) -> OrderedDict:
        config_entries = OrderedDict()
        config_entries['SECONDS_PER_SLOT'] = mainnet_config_defaults['SECONDS_PER_SLOT']
        config_entries['SECONDS_PER_ETH1_BLOCK'] = self.etb_config.get('seconds-per-eth1-block')
        config_entries['MIN_VALIDATOR_WITHDRAWABILITY_DELAY'] = self.etb_config.get('min-validator-withdrawability-delay')
        config_entries['SHARD_COMMITTEE_PERIOD'] = self.etb_config.get('shard-committee-period')
        config_entries['ETH1_FOLLOW_DISTANCE'] = self.etb_config.get('eth1-follow-distance')
        return config_entries

    def get_validator_cycle_config_values(self) -> OrderedDict:
        config_entries = OrderedDict()
        config_entries['INACTIVITY_SCORE_BIAS'] = mainnet_config_defaults['INACTIVITY_SCORE_BIAS']
        config_entries['INACTIVITY_SCORE_RECOVERY_RATE'] = mainnet_config_defaults['INACTIVITY_SCORE_RECOVERY_RATE']
        config_entries['EJECTION_BALANCE'] = mainnet_config_defaults['EJECTION_BALANCE']
        config_entries['MIN_PER_EPOCH_CHURN_LIMIT'] = mainnet_config_defaults['MIN_PER_EPOCH_CHURN_LIMIT']
        config_entries['CHURN_LIMIT_QUOTIENT'] = mainnet_config_defaults['CHURN_LIMIT_QUOTIENT']
        return config_entries

    def get_fork_choice_config_values(self) -> OrderedDict:
        config_entries = OrderedDict()
        config_entries['PROPOSER_SCORE_BOOST'] = mainnet_config_defaults['PROPOSER_SCORE_BOOST']
        return config_entries

    def get_transition_config_values(self) -> OrderedDict:
        config_entries = OrderedDict()
        config_entries['TERMINAL_TOTAL_DIFFICULTY'] = self.etb_config.get('terminal-total-difficulty')
        config_entries['TERMINAL_BLOCK_HASH'] = self.etb_config.get('terminal-block-hash')
        config_entries['TERMINAL_BLOCK_HASH_ACTIVATION_EPOCH'] = self.etb_config.get('terminal-block-hash-activation'
                                                                                     '-epoch')
        return config_entries

    def get_misc_config_values(self) -> OrderedDict:
        config_entries = OrderedDict()
        config_entries['MAX_COMMITTEES_PER_SLOT'] = mainnet_config_defaults['MAX_COMMITTEES_PER_SLOT']

        return config_entries

    def get_config_yaml_as_str(self) -> str:
        """We do this as a string soley to make them readable for debugging purposes"""
        yaml_as_str = f"PRESET_BASE: '{self.etb_config.get('preset-base')}'\n"
        yaml_as_str += f"CONFIG_NAME: '{self.etb_config.get('config-name')}'\n"
        yaml_as_str += "# Genesis\n# ---------------------------------------------------------------\n"
        for k, v in self.get_genesis_config_values().items():
            yaml_as_str += f"{k}: {v}\n"
        yaml_as_str += "# Forking\n# ---------------------------------------------------------------\n"
        for k, v in self.get_forking_config_values().items():
            yaml_as_str += f"{k}: {v}\n"
        yaml_as_str += "# Time Parameters\n# ---------------------------------------------------------------\n"
        for k, v in self.get_time_parameters_config_values().items():
            yaml_as_str += f"{k}: {v}\n"
        yaml_as_str += "# Validator Cycle\n# ---------------------------------------------------------------\n"
        for k, v in self.get_validator_cycle_config_values().items():
            yaml_as_str += f"{k}: {v}\n"
        yaml_as_str += "# Fork Choice\n# ---------------------------------------------------------------\n"
        for k, v in self.get_fork_choice_config_values().items():
            yaml_as_str += f"{k}: {v}\n"
        yaml_as_str += "# Transition\n# ---------------------------------------------------------------\n"
        for k, v in self.get_transition_config_values().items():
            yaml_as_str += f"{k}: {v}\n"
        yaml_as_str += "# Deposit Contract\n# ---------------------------------------------------------------\n"
        for k, v in self.get_deposit_config_values().items():
            yaml_as_str += f"{k}: {v}\n"
        yaml_as_str += "# Misc\n# ---------------------------------------------------------------\n"
        for k, v in self.get_misc_config_values().items():
            yaml_as_str += f"{k}: {v}\n"

        return yaml_as_str

    def get_config_yaml(self) -> OrderedDict:
        config = {}
        config['PRESET_BASE'] = self.etb_config.get('preset-base')
        config['CONFIG_NAME'] = self.etb_config.get('config-name')
        for k, v in self.get_genesis_config_values().items():
            config[k] = v
        for k, v in self.get_forking_config_values().items():
            config[k] = v
        for k, v in self.get_time_parameters_config_values().items():
            config[k] = v
        for k, v in self.get_validator_cycle_config_values().items():
            config[k] = v
        for k, v in self.get_fork_choice_config_values().items():
            config[k] = v
        for k, v in self.get_transition_config_values().items():
            config[k] = v
        for k, v in self.get_deposit_config_values().items():
            config[k] = v
        for k, v in self.get_misc_config_values().items():
            config[k] = v

        return config

    def get_old_version_yaml(self) -> str:
        # prysm doesn't actually use yaml for parsing these for some reason.
        config = self.get_config_yaml()
        return f"""
# Extends the mainnet preset
PRESET_BASE: '{config['PRESET_BASE']}'
CONFIG_NAME: '{config['CONFIG_NAME']}'

# Genesis
# ---------------------------------------------------------------
# `2**14` (= 16,384)
MIN_GENESIS_ACTIVE_VALIDATOR_COUNT: {config['MIN_GENESIS_ACTIVE_VALIDATOR_COUNT']}

# This is an invalid valid and should be updated when you create the genesis
MIN_GENESIS_TIME: {config['MIN_GENESIS_TIME']}
GENESIS_FORK_VERSION: {config['GENESIS_FORK_VERSION']}
GENESIS_DELAY: {config['GENESIS_DELAY']}


# Forking
# ---------------------------------------------------------------
# Some forks are disabled for now:
#  - These may be re-assigned to another fork-version later
#  - Temporarily set to max uint64 value: 2**64 - 1

# Altair
ALTAIR_FORK_VERSION: {config['ALTAIR_FORK_VERSION']}
ALTAIR_FORK_EPOCH: {config['ALTAIR_FORK_EPOCH']}
# Merge
BELLATRIX_FORK_VERSION: {config['BELLATRIX_FORK_VERSION']}
BELLATRIX_FORK_EPOCH: {config['BELLATRIX_FORK_EPOCH']}

TERMINAL_TOTAL_DIFFICULTY: {config['TERMINAL_TOTAL_DIFFICULTY']}
TERMINAL_BLOCK_HASH: {config['TERMINAL_BLOCK_HASH']}
TERMINAL_BLOCK_HASH_ACTIVATION_EPOCH: {config['TERMINAL_BLOCK_HASH_ACTIVATION_EPOCH']}

# Capella
CAPELLA_FORK_VERSION: {config['CAPELLA_FORK_VERSION']}
CAPELLA_FORK_EPOCH: {config['CAPELLA_FORK_EPOCH']}

# EIP4844
EIP4844_FORK_VERSION: {config['EIP4844_FORK_VERSION']}
EIP4844_FORK_EPOCH: {config['EIP4844_FORK_EPOCH']}

# Time parameters
# ---------------------------------------------------------------
# 12 seconds
SECONDS_PER_SLOT: {config['SECONDS_PER_SLOT']}
# 14 (estimate from Eth1 mainnet)
SECONDS_PER_ETH1_BLOCK: {config['SECONDS_PER_ETH1_BLOCK']}
# 2**8 (= 256) epochs ~27 hours
MIN_VALIDATOR_WITHDRAWABILITY_DELAY: {config['MIN_VALIDATOR_WITHDRAWABILITY_DELAY']}
# 2**8 (= 256) epochs ~27 hours
SHARD_COMMITTEE_PERIOD: {config['SHARD_COMMITTEE_PERIOD']}
# 2**11 (= 2,048) Eth1 blocks ~8 hours
ETH1_FOLLOW_DISTANCE: {config['ETH1_FOLLOW_DISTANCE']}


# Validator cycle
# ---------------------------------------------------------------
# 2**2 (= 4)
INACTIVITY_SCORE_BIAS: {config['INACTIVITY_SCORE_BIAS']}
# 2**4 (= 16)
INACTIVITY_SCORE_RECOVERY_RATE: {config['INACTIVITY_SCORE_RECOVERY_RATE']}
# 2**4 * 10**9 (= 16,000,000,000) Gwei
EJECTION_BALANCE: {config['EJECTION_BALANCE']}
# 2**2 (= 4)
MIN_PER_EPOCH_CHURN_LIMIT: {config['MIN_PER_EPOCH_CHURN_LIMIT']}
# 2**16 (= 65,536)
CHURN_LIMIT_QUOTIENT: {config['CHURN_LIMIT_QUOTIENT']}

# Fork choice
# ---------------------------------------------------------------
# 40%
PROPOSER_SCORE_BOOST: 40

# Deposit contract
# ---------------------------------------------------------------
DEPOSIT_CHAIN_ID: {config['DEPOSIT_CHAIN_ID']}
DEPOSIT_NETWORK_ID: {config['DEPOSIT_NETWORK_ID']}
DEPOSIT_CONTRACT_ADDRESS: {config['DEPOSIT_CONTRACT_ADDRESS']}
"""
