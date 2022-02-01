from ruamel import yaml
import subprocess


def deploy_consensus_genesis(global_config):
    """
    We just leverage the eth2-testnet-genesis utility.
    currently only using mainnet preset.
    """
    genesis_fork = global_config["config-params"]["consensus-layer"]["forks"][
        "genesis-fork-name"
    ]
    mnemonic = global_config["accounts"]["validator-mnemonic"]
    config = global_config["files"]["consensus-config"]
    state_out = global_config["files"]["consensus-genesis"]

    with open("/tmp/validators.yaml", "w") as f:
        yaml.dump(
            [
                {
                    "mnemonic": mnemonic,
                    "count": global_config["config-params"]["consensus-layer"][
                        "min-genesis-active-validator-count"
                    ],
                }
            ],
            f,
        )

    cmd = [
        "eth2-testnet-genesis",
        genesis_fork,
        "--mnemonics",
        "/tmp/validators.yaml",
        "--config",
        config,
        "--state-output",
        state_out,
    ]

    subprocess.run(cmd)
