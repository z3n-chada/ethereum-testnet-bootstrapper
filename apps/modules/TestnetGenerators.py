import pathlib
import shutil
import subprocess


class TestnetDirectoryGenerator(object):
    """
    Generic TestnetDirectoryGenerator. Given a ConsensusClient it generates the required
    directory structure for the client to start up.
    """

    def __init__(self, consensus_client, password=None):
        self.client = consensus_client
        self.password = password

        # self.etb_config = consensus_client.etb_config
        self.mnemonic = self.client.get("validator-mnemonic")

        genesis_ssz = self.client.get("consensus-genesis-file")
        consensus_config = self.client.get("consensus-config-file")
        self.testnet_dir = pathlib.Path(self.client.get("testnet-dir"))
        self.validator_dir = pathlib.Path(
            self.client.get("testnet-dir") + "/validators/"
        )

        if self.testnet_dir.exists():
            print(f"WARNING: {self.testnet_dir} already exists", flush=True)
            # shutil.rmtree(str(self.testnet_dir))  # clean old run

        self.testnet_dir.mkdir(exist_ok=True)
        self.validator_dir.mkdir(exist_ok=True)

        shutil.copy(genesis_ssz, str(self.testnet_dir) + "/genesis.ssz")
        shutil.copy(consensus_config, str(self.testnet_dir) + "/config.yaml")

        self._generate_validator_stores()

    def _generate_validator_stores(self):
        """
        Clients have a validator offset start (which specifies the offset
        from which we generate their keys.

        The Clients Consensus-Config specifies the number of validators per
        node, and the client specifies the number of nodes. Thus to have
        mulitple clients you must ensure that the validator offsets between
        each client is atleast num_nodes*num_validators above the previous
        client.

        You can check this using the ETBConfig.check_configuration_sanity()
        """

        validator_offset_start = self.client.get("validator-offset-start")
        num_validators = self.client.get("num-validators")
        for x in range(self.client.get("num-nodes")):

            source_min = validator_offset_start + (x * num_validators)
            source_max = source_min + num_validators
            cmd = (
                "eth2-val-tools keystores "
                + f"--out-loc {self.validator_dir}/node_{x} "
                + f"--source-min {source_min} "
                + f"--source-max {source_max} "
                + f'--source-mnemonic "{self.mnemonic}"'
            )
            if self.password is not None:
                cmd += f' --prysm-pass "{self.password}"'
            subprocess.run(cmd, shell=True)


class TekuTestnetDirectoryGenerator(TestnetDirectoryGenerator):
    def __init__(self, consensus_client):
        super().__init__(consensus_client)

    def finalize_testnet_dir(self):
        for ndx in range(self.client.get("num-nodes")):
            node_dir = pathlib.Path(str(self.testnet_dir) + f"/node_{ndx}")
            node_dir.mkdir()
            keystore_dir = pathlib.Path(str(self.testnet_dir) + "/validators")
            src_dir = pathlib.Path(str(keystore_dir) + f"/node_{ndx}")
            shutil.copytree(str(src_dir) + "/teku-keys", str(node_dir) + "/keys")
            shutil.copytree(str(src_dir) + "/teku-secrets", str(node_dir) + "/secrets")

        shutil.rmtree(str(self.testnet_dir) + "/validators/")


class PrysmTestnetGenerator(TestnetDirectoryGenerator):
    def __init__(self, consensus_client):
        super().__init__(
            consensus_client,
            consensus_client.get("validator-password"),
        )
        # prysm only stuff.
        self.password_file = self.client.get("wallet-path")

        with open(self.password_file, "w") as f:
            f.write(self.password)

    def finalize_testnet_dir(self):
        """
        Copy validator info into local client.
        """
        print(f"Finalizing prysm client {self.testnet_dir} testnet directory.")
        for ndx in range(self.client.get("num-nodes")):
            node_dir = pathlib.Path(str(self.testnet_dir) + f"/node_{ndx}")
            node_dir.mkdir()
            keystore_dir = pathlib.Path(
                str(self.testnet_dir) + f"/validators/node_{ndx}/"
            )
            for f in keystore_dir.glob("prysm/*"):
                if f.is_dir():
                    shutil.copytree(src=f, dst=f"{node_dir}/{f.name}")
                else:
                    shutil.copy(src=f, dst=f"{node_dir}/{f.name}")
        # done now clean up..
        shutil.rmtree(str(self.testnet_dir) + "/validators/")


class LighthouseTestnetGenerator(TestnetDirectoryGenerator):
    def __init__(self, consensus_client):
        super().__init__(consensus_client)

        with open(str(self.testnet_dir) + "/deploy_block.txt", "w") as f:
            f.write("0")

    def finalize_testnet_dir(self):
        """
        Copy validator info into local client.
        """
        print(f"Finalizing lighthouse client dir={self.testnet_dir}")
        for ndx in range(self.client.get("num-nodes")):
            node_dir = pathlib.Path(str(self.testnet_dir) + f"/node_{ndx}")
            node_dir.mkdir()
            keystore_dir = pathlib.Path(str(self.testnet_dir) + "/validators")
            src_dir = pathlib.Path(str(keystore_dir) + f"/node_{ndx}")
            shutil.copytree(str(src_dir) + "/keys", str(node_dir) + "/keys")
            shutil.copytree(str(src_dir) + "/secrets", str(node_dir) + "/secrets")
        # done now clean up..
        shutil.rmtree(str(self.testnet_dir) + "/validators/")


class NimbusTestnetGenerator(TestnetDirectoryGenerator):
    def __init__(self, consensus_client):
        super().__init__(consensus_client)

    def finalize_testnet_dir(self):
        """
        Copy validator info into local client.
        """
        print(f"Finalizing nimbus client dir={self.testnet_dir}")
        for ndx in range(self.client.get("num-nodes")):
            node_dir = pathlib.Path(str(self.testnet_dir) + f"/node_{ndx}")
            node_dir.mkdir()
            keystore_dir = pathlib.Path(str(self.testnet_dir) + "/validators")
            src_dir = pathlib.Path(str(keystore_dir) + f"/node_{ndx}")
            shutil.copytree(str(src_dir) + "/nimbus-keys", str(node_dir) + "/keys")
            shutil.copytree(str(src_dir) + "/secrets", str(node_dir) + "/secrets")
        # done now clean up..
        shutil.rmtree(str(self.testnet_dir) + "/validators/")

        # just in case set a deposit deploy block.
        with open(f"{str(self.testnet_dir)}/deposit_contract_block.txt", "w") as f:
            f.write(
                "0x0000000000000000000000000000000000000000000000000000000000000000"
            )


class LodestarTestnetGenerator(TestnetDirectoryGenerator):
    def __init__(self, consensus_client):
        super().__init__(consensus_client)

    def finalize_testnet_dir(self):
        """
        Copy validator info into local client.
        """
        for ndx in range(self.client.get("num-nodes")):
            node_dir = pathlib.Path(str(self.testnet_dir) + f"/node_{ndx}")
            node_dir.mkdir()
            keystore_dir = pathlib.Path(str(self.testnet_dir) + "/validators")
            src_dir = pathlib.Path(str(keystore_dir) + f"/node_{ndx}")
            shutil.copytree(str(src_dir) + "/keys", str(node_dir) + "/keys")
            shutil.copytree(
                str(src_dir) + "/lodestar-secrets", str(node_dir) + "/secrets"
            )
            validator_db = pathlib.Path(str(node_dir) + "/validatordb")
            validator_db.mkdir()
        # done now clean up..
        shutil.rmtree(str(self.testnet_dir) + "/validators/")


def generate_consensus_testnet_dirs(global_config):
    generators = {
        "teku": TekuTestnetDirectoryGenerator,
        "prysm": PrysmTestnetGenerator,
        "lighthouse": LighthouseTestnetGenerator,
        "nimbus": NimbusTestnetGenerator,
        "lodestar": LodestarTestnetGenerator,
    }
    for name, client in global_config.get_consensus_clients().items():
        print(f"Creating testnet directory for {name}")
        ccg = generators[client.get("client-name")](client)
        ccg.finalize_testnet_dir()
