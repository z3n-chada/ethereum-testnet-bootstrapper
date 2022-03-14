import pathlib
import shutil
import subprocess


class TestnetDirectoryGenerator(object):
    def __init__(self, global_config, client_config, password=None):
        self.gc = global_config
        self.cc = client_config
        self.ccc = global_config["consensus-configs"][client_config["consensus-config"]]
        self.password = password
        self.mnemonic = self.gc["accounts"]["validator-mnemonic"]

        genesis_ssz = self.gc["files"]["consensus-genesis"]
        consensus_config = self.gc["files"]["consensus-config"]
        self.testnet_dir = pathlib.Path(self.cc["testnet-dir"])
        validator_dir = pathlib.Path(self.cc["testnet-dir"] + "/validators/")
        if self.testnet_dir.exists():
            print(f"WARNING: {self.testnet_dir} already exists", flush=True)
            # shutil.rmtree(str(self.testnet_dir))  # clean old run

        self.testnet_dir.mkdir(exist_ok=True)
        validator_dir.mkdir(exist_ok=True)

        shutil.copy(genesis_ssz, str(self.testnet_dir) + "/genesis.ssz")
        shutil.copy(consensus_config, str(self.testnet_dir) + "/config.yaml")

        self._generate_validator_stores(
            self.cc["validator-offset-start"],
            self.ccc["num-nodes"],
            self.ccc["num-validators"],
            str(validator_dir),
            password=self.password,
        )

    def _generate_validator_stores(
        self, start, num_nodes, num_validators, out_dir, password=None
    ):
        divisor = int(num_validators / num_nodes)
        if num_validators % num_nodes != 0:
            raise Exception("Validators must evenly divide nodes")

        curr_offset = start
        for x in range(num_nodes):
            val_dir = f"node_{x}"
            cmd = (
                f"eth2-val-tools keystores --out-loc {out_dir}/{val_dir} "
                + f"--source-min {curr_offset} --source-max {curr_offset + divisor} "
                + f'--source-mnemonic "{self.mnemonic}"'
            )
            if password is not None:
                cmd += f' --prysm-pass "{password}"'
            subprocess.run(cmd, shell=True)
            curr_offset += divisor


class TekuTestnetDirectoryGenerator(TestnetDirectoryGenerator):
    def __init__(self, global_config, client_config):
        super().__init__(global_config, client_config)

    def finalize_testnet_dir(self):
        for ndx in range(self.ccc["num-nodes"]):
            node_dir = pathlib.Path(str(self.testnet_dir) + f"/node_{ndx}")
            node_dir.mkdir()
            keystore_dir = pathlib.Path(str(self.testnet_dir) + "/validators")
            src_dir = pathlib.Path(str(keystore_dir) + f"/node_{ndx}")
            shutil.copytree(str(src_dir) + "/teku-keys", str(node_dir) + "/keys")
            shutil.copytree(str(src_dir) + "/teku-secrets", str(node_dir) + "/secrets")

        shutil.rmtree(str(self.testnet_dir) + "/validators/")


class PrysmTestnetGenerator(TestnetDirectoryGenerator):
    def __init__(self, global_config, client_config):

        super().__init__(
            global_config,
            client_config,
            client_config["consensus-additional-env"]["validator-password"],
        )
        # prysm only stuff.
        self.password_file = self.cc["consensus-additional-env"]["wallet-path"]

        with open(self.password_file, "w") as f:
            f.write(self.password)

    def finalize_testnet_dir(self):
        """
        Copy validator info into local client.
        """
        print(f"Finalizing prysm client {self.testnet_dir} testnet directory.")
        for ndx in range(self.ccc["num-nodes"]):
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
    def __init__(self, global_config, client_config):
        super().__init__(global_config, client_config)
        with open(str(self.testnet_dir) + "/deploy_block.txt", "w") as f:
            f.write("0")

    def finalize_testnet_dir(self):
        """
        Copy validator info into local client.
        """
        print(f"Finalizing lighthouse client dir={self.testnet_dir}")
        for ndx in range(self.ccc["num-nodes"]):
            node_dir = pathlib.Path(str(self.testnet_dir) + f"/node_{ndx}")
            node_dir.mkdir()
            keystore_dir = pathlib.Path(str(self.testnet_dir) + "/validators")
            src_dir = pathlib.Path(str(keystore_dir) + f"/node_{ndx}")
            shutil.copytree(str(src_dir) + "/keys", str(node_dir) + "/keys")
            shutil.copytree(str(src_dir) + "/secrets", str(node_dir) + "/secrets")
        # done now clean up..
        shutil.rmtree(str(self.testnet_dir) + "/validators/")


class NimbusTestnetGenerator(TestnetDirectoryGenerator):
    def __init__(self, global_config, client_config):
        super().__init__(global_config, client_config)

    def finalize_testnet_dir(self):
        """
        Copy validator info into local client.
        """
        print(f"Finalizing lighthouse client dir={self.testnet_dir}")
        for ndx in range(self.ccc["num-nodes"]):
            node_dir = pathlib.Path(str(self.testnet_dir) + f"/node_{ndx}")
            node_dir.mkdir()
            keystore_dir = pathlib.Path(str(self.testnet_dir) + "/validators")
            src_dir = pathlib.Path(str(keystore_dir) + f"/node_{ndx}")
            shutil.copytree(str(src_dir) + "/nimbus-keys", str(node_dir) + "/keys")
            shutil.copytree(str(src_dir) + "/secrets", str(node_dir) + "/secrets")
        # done now clean up..
        shutil.rmtree(str(self.testnet_dir) + "/validators/")

        # just in case set a deposit deploy block.
        with open(f"{str(self.testnet_dir)}/deposit_contract_block.txt", 'w') as f:
            f.write("0x0000000000000000000000000000000000000000000000000000000000000000")


def generate_consensus_testnet_dirs(global_config):
    generators = {
        "teku": TekuTestnetDirectoryGenerator,
        "prysm": PrysmTestnetGenerator,
        "lighthouse": LighthouseTestnetGenerator,
        "nimbus": NimbusTestnetGenerator,
    }
    for cc in global_config["consensus-clients"]:
        print(f"Creating testnet directory for {cc}")
        c_config = global_config["consensus-clients"][cc]
        c_client = c_config["client-name"]
        ccg = generators[c_client](global_config, c_config)
        ccg.finalize_testnet_dir()
