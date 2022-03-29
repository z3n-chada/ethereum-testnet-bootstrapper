import subprocess

from ruamel import yaml


def deploy_consensus_genesis(
    etb_config,
    eth1_block_hash="0000000000000000000000000000000000000000000000000000000000000000",
    eth1_timestamp=1644722881,
    preset_base="mainnet",
):
    """
    We just leverage the eth2-testnet-genesis utility.
    currently only using mainnet preset.
    """
    genesis_fork = etb_config.get("genesis-fork-name")
    mnemonic = etb_config.get("validator-mnemonic")
    config = etb_config.get("consensus-config-file")
    state_out = etb_config.get("consensus-genesis-file")

    with open("/tmp/validators.yaml", "w") as f:
        yaml.dump(
            [
                {
                    "mnemonic": mnemonic,
                    "count": etb_config.get("min-genesis-active-validator-count"),
                }
            ],
            f,
        )

    cmd = [
        "eth2-testnet-genesis",
        genesis_fork,
        "--preset-phase0",
        preset_base,
        "--mnemonics",
        "/tmp/validators.yaml",
        "--config",
        config,
        "--state-output",
        state_out,
        "--eth1-block",
        eth1_block_hash,
        "--timestamp",
        str(eth1_timestamp),
    ]
    subprocess.run(cmd)
