"""
    This module is the glue to tie together all the execution and consensus client bootstrapping
    phases. There is a high level doc in docs that discusses this process.
"""
import json
import logging
import os
import pathlib
import random
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict

from ruamel import yaml

from .ConsensusGenesis import ConsensusConfigurationWriter, ConsensusGenesisWriter
from .ETBConfig import ETBConfig, ConsensusClient, ETBClient, ForkVersion
from .ExecutionGenesis import ExecutionGenesisWriter
from .ExecutionRPC import (ETBExecutionRPC, admin_add_peer_RPC,
                           admin_node_info_RPC, personal_unlock_account_RPC, miner_start_RPC)

logger = logging.getLogger("bootstrapper_log")


class EthereumTestnetBootstrapper(object):
    """
    The Testnet Bootstrapper wraps all the consensus and execution
    bootstrapper logic to bootstrap all the clients. It also handles
    the consensus bootnode.

    The EthereumTestnetBootstrapper is used to init the testnet and later is
    used to bootstrap and run the testnet.
    """

    def __init__(self, config_path):
        self.etb_config = ETBConfig(config_path)
        self.config_path = config_path

    def init_testnet(self):
        """
        The init routine simply processes the etb-config file and performs all
        the work that can be done statically. This includes creating the dir
        structure for the testnet and populating the cl bootnode enr file.
        """
        # clear the last run
        self.clear_last_run()

        # create the testnet root
        Path(self.etb_config.get("testnet-dir")).mkdir()

        # create dirs
        self._create_client_testnet_directories()

        # create other static files
        self._create_consensus_bootnode_dir()  # where we write the bootnode enr for CLs
        self._write_client_jwt_secrets()

        self.etb_config.write_to_docker_compose()

        # copy in the config file we used for the init process.
        shutil.copy(self.config_path, self.etb_config.get("etb-config-file"))

    def bootstrap_testnet(self):
        """
        This routine bootstraps the testnet. The general process is as follows:
        1. open the etb_config file and write the current time.
        2. signal the consensus bootnode to come online.
        3. create the execution genesis files and then signal those clients to
           come online.
        4. pair all the el clients.
        5. create the consensus genesis files and then signal those clients to
            come online

        """
        # set the bootstrap time and update the file. Then signal dockers via
        # checkpoint.
        self.etb_config.set_genesis_time(int(time.time()))
        self.etb_config.write_config_to_file()

        self.etb_config.write_checkpoint_file("etb-config-checkpoint-file")

        # signal the consensus bootnode is ready to come online.
        self.etb_config.write_checkpoint_file("consensus-bootnode-checkpoint-file")

        # bootstrap all the execution clients.
        self._write_execution_genesis_files()
        self.etb_config.write_checkpoint_file("execution-checkpoint-file")

        # pair all the EL clients together.
        self._pair_el_clients(self._get_all_el_enodes())

        # if needed we start the clique miners
        if self.etb_config.get_genesis_fork() < ForkVersion.Bellatrix:
            self._start_clique_miners()

        # bootstrap all the consensus clients.
        self._write_consensus_genesis_files()
        # cl_bootstrapper.bootstrap_consensus_clients()
        self.etb_config.write_checkpoint_file("consensus-checkpoint-file")

    def clear_last_run(self):
        """
        Clear all the files and dirs present in the testnet-root.
        """
        testnet_root = self.etb_config.get("testnet-root")
        if Path(testnet_root).exists():
            for file in os.listdir(testnet_root):
                path = Path(os.path.join(testnet_root, file))
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()

    # General private helpers to keep functions short.

    def _start_clique_miners(self) -> None:
        """
        When using clique (pre-merge) we must unlock the signing account
        on one of the EL clients and begin mining. By default, we only use
        one signer, and that signer is the key used in the first premine.

        The instance that starts mining is the first entry of the first client
        that implements the api. By default, we use alphabetical order.
        :return: None
        """
        possible_el_clients = self.etb_config.get_execution_rpc_paths(protocol='http', apis=['personal','miner','clique'])
        if len(possible_el_clients) == 0:
            raise Exception("Error: Couldn't start clique miners as no EL client implements personal and miner")
        logger.debug(f"Found possible clique miners: {possible_el_clients}")
        names = list(possible_el_clients.keys())
        names.sort()

        miner_name = names[0]
        logger.info(f"Starting clique miner for: {miner_name} : {possible_el_clients[miner_name]}")

        address = self.etb_config.get_clique_signer()
        passphrase = self.etb_config.get('eth1-passphrase')

        unlock_rpc = personal_unlock_account_RPC(address=address, passphrase=passphrase, duration=100000)
        miner_rpc = miner_start_RPC(1)

        etb_rpc = ETBExecutionRPC(self.etb_config, timeout=5)
        etb_rpc.do_rpc_request(unlock_rpc, client_nodes=[miner_name], all_clients=False)
        etb_rpc.do_rpc_request(miner_rpc, client_nodes=[miner_name], all_clients=False)

    def _create_consensus_bootnode_dir(self):
        """
        Populate the enr file to be used by the consensus bootnode.
        """
        # handle the consensus bootnode enr files:
        enr_path = Path(self.etb_config.get("consensus-bootnode-file"))
        enr_path.parents[0].mkdir(exist_ok=True)

    def _get_all_el_enodes(self, protocol='http') -> Dict[str, str]:
        """
        fetch the EL enodes for all clients that implement the admin RPC
        interface.

        returns: dict {client-name : enode,...}
        """
        enodes = {}

        etb_rpc = ETBExecutionRPC(self.etb_config, timeout=5)
        clients_with_admin_interface = []
        for client, apis in self.etb_config.get_all_execution_clients_and_apis().items():
            if 'admin' in apis:
                clients_with_admin_interface.append(client)

        node_info = etb_rpc.do_rpc_request(admin_node_info_RPC(), client_nodes=clients_with_admin_interface, all_clients=False)

        for name, node_info_resp in node_info.items():
            enodes[name] = node_info_resp["result"]["enode"]

        return enodes

    def _pair_el_clients(self, enode_dict, optional_delay=0):
        """
            Given a dict of enodes, iterate through it and pair the clients via
            the admin RPC interface.
        """
        etb_rpc = ETBExecutionRPC(self.etb_config, timeout=5)

        # iterate through all clients and enodes and peer them together.
        for client, enode in enode_dict.items():
            clients_to_peer = list(enode_dict.keys())
            # don't peer a client with itself.
            clients_to_peer.remove(client)
            etb_rpc.do_rpc_request(
                admin_add_peer_RPC(enode),
                client_nodes=clients_to_peer,
                all_clients=False,
            )
            time.sleep(optional_delay)

    def _create_client_testnet_directories(self):
        """
        Create the testnet directory structure of the testnet for init purposes

        iterate through the etb clients and create their required dirs.
        The dir structure for a client is:
            /{testnet_dir}/node_{node_num}/{execution-client}
        """
        logger.info("Creating client testnet dirs.")
        for multi_clients in self.etb_config.get_clients().values():
            root_dir = Path(multi_clients.get("testnet-dir"))
            root_dir.mkdir()
            for client in multi_clients:
                print(client)
                node_dir = Path(client.get_node_dir())
                el_path = Path(node_dir.joinpath(f"{client.get('execution-client')}"))
                node_dir.mkdir()
                el_path.mkdir()

    def _write_client_jwt_secrets(self):
        logger.info("Creating client jwt-secrets")
        for multi_clients in self.etb_config.get_clients().values():
            for client in multi_clients:
                jwt_secret_file = client.get("jwt-secret-file")
                jwt_secret = f"0x{random.randbytes(32).hex()}"
                with open(jwt_secret_file, "w") as f:
                    f.write(jwt_secret)

    def _write_execution_genesis_files(self) -> None:
        """
            Writes all the execution genesis json files for EL clients to the
            file paths specified in the etb-config.
        """

        egw = ExecutionGenesisWriter(self.etb_config)

        # TODO: see that hacky workaround post in ETBConfig::get()
        # if not self.etb_config.has("bootstrap-genesis"):
        #     raise Exception("Cannot write execution genesis files before bootstrapping.")

        with open(self.etb_config.get('geth-genesis-file'), 'w') as f:
            f.write(json.dumps(egw.create_geth_genesis()))

        with open(self.etb_config.get('besu-genesis-file'), 'w') as f:
            f.write(json.dumps(egw.create_besu_genesis()))

        with open(self.etb_config.get('nether-mind-genesis-file'), 'w') as f:
            f.write(json.dumps(egw.create_nethermind_genesis()))

    def _write_consensus_genesis_files(self):
        """
        Create the consensus config.yaml file and the genesis.ssz file.
        """
        logger.info("ConsensusBootstrapper bootstrapping consensus..")
        ccw = ConsensusConfigurationWriter(self.etb_config)
        cgw = ConsensusGenesisWriter(self.etb_config)
        with open(self.etb_config.get("consensus-config-file"), "w") as f:
            f.write(ccw.get_old_version_yaml())
        logger.debug("ConsensusBootstrapper wrote config.yaml")
        with open(self.etb_config.get("consensus-genesis-file"), "wb") as f:
            f.write(cgw.create_consensus_genesis())
        logger.debug("ConsensusBootstrapper wrote genesis.ssz")
        # we have everything we need to populate all the consensus directories

        generators = {
            "teku": TekuConsensusDirectoryGenerator,
            "prysm": PrysmTestnetGenerator,
            "lighthouse": LighthouseTestnetGenerator,
            "nimbus": NimbusTestnetGenerator,
            "lodestar": LodestarTestnetGenerator,
        }
        for name, client in self.etb_config.get_clients().items():
            logger.info(f"Creating testnet directory for {name}")
            cdg = generators[client.get('consensus-client')](client)
            cdg.finalize_testnet_dir()


class ConsensusDirectoryGenerator(object):
    """
    Generic ConsensusDirectoryGenerator. Given a ConsensusClient it generates the required
    directory structure for the client to start up as well as populating the directories with
    all the required files, e.g. genesis ssz, config files, etc.
    """

    def __init__(self, client_module: ETBClient, password=None):
        self.client_module = client_module
        self.password = password

        # self.etb_config = consensus_client.etb_config
        self.mnemonic = self.client_module.etb_config.get('validator-mnemonic')
        # self.mnemonic = self.client.get("validator-mnemonic")

        genesis_ssz = self.client_module.etb_config.get("consensus-genesis-file")
        consensus_config = self.client_module.etb_config.get("consensus-config-file")
        self.testnet_dir = pathlib.Path(self.client_module.get("testnet-dir"))
        self.validator_dir = pathlib.Path(
            self.client_module.get("testnet-dir") + "/validators/"
        )

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
        multiple clients you must ensure that the validator offsets between
        each client is at least num_nodes*num_validators above the previous
        client.

        You can check this using the ETBConfig.check_configuration_sanity()
        """

        validator_offset_start = self.client_module.get("validator-offset-start")
        num_validators = self.client_module.consensus_config.config["num-validators"] #TODO: make this not shit.
        for x in range(self.client_module.get("num-nodes")):

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


class TekuConsensusDirectoryGenerator(ConsensusDirectoryGenerator):
    def __init__(self, consensus_client):
        super().__init__(consensus_client)

    def finalize_testnet_dir(self):
        for ndx in range(self.client_module.get("num-nodes")):
            node_dir = pathlib.Path(str(self.testnet_dir) + f"/node_{ndx}")
            keystore_dir = pathlib.Path(str(self.testnet_dir) + "/validators")
            src_dir = pathlib.Path(str(keystore_dir) + f"/node_{ndx}")
            shutil.copytree(str(src_dir) + "/teku-keys", str(node_dir) + "/keys")
            shutil.copytree(str(src_dir) + "/teku-secrets", str(node_dir) + "/secrets")

        shutil.rmtree(str(self.testnet_dir) + "/validators/")


class PrysmTestnetGenerator(ConsensusDirectoryGenerator):
    def __init__(self, consensus_client: ETBClient):
        # super hacky workaround to get this to work. TODO: make this work nicely with new ETB.
        validator_password = consensus_client.config.config['additional-env']['validator-password']
        super().__init__(
            consensus_client,
            validator_password,
        )
        # prysm only stuff.
        self.password_file = self.client_module.config.config["additional-env"]["wallet-path"]

        with open(self.password_file, "w") as f:
            f.write(self.password)

    def finalize_testnet_dir(self):
        """
        Copy validator info into local client.
        """
        print(f"Finalizing prysm client {self.testnet_dir} testnet directory.")
        for ndx in range(self.client_module.get("num-nodes")):
            node_dir = pathlib.Path(str(self.testnet_dir) + f"/node_{ndx}")
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


class LighthouseTestnetGenerator(ConsensusDirectoryGenerator):
    def __init__(self, consensus_client):
        super().__init__(consensus_client)

        with open(str(self.testnet_dir) + "/deploy_block.txt", "w") as f:
            f.write("0")

    def finalize_testnet_dir(self):
        """
        Copy validator info into local client.
        """
        print(f"Finalizing lighthouse client dir={self.testnet_dir}")
        for ndx in range(self.client_module.get("num-nodes")):
            node_dir = pathlib.Path(str(self.testnet_dir) + f"/node_{ndx}")
            keystore_dir = pathlib.Path(str(self.testnet_dir) + "/validators")
            src_dir = pathlib.Path(str(keystore_dir) + f"/node_{ndx}")
            shutil.copytree(str(src_dir) + "/keys", str(node_dir) + "/keys")
            shutil.copytree(str(src_dir) + "/secrets", str(node_dir) + "/secrets")
        # done now clean up..
        shutil.rmtree(str(self.testnet_dir) + "/validators/")


class NimbusTestnetGenerator(ConsensusDirectoryGenerator):
    def __init__(self, consensus_client):
        super().__init__(consensus_client)

    def finalize_testnet_dir(self):
        """
        Copy validator info into local client.
        """
        print(f"Finalizing nimbus client dir={self.testnet_dir}")
        for ndx in range(self.client_module.get("num-nodes")):
            node_dir = pathlib.Path(str(self.testnet_dir) + f"/node_{ndx}")
            keystore_dir = pathlib.Path(str(self.testnet_dir) + "/validators")
            src_dir = pathlib.Path(str(keystore_dir) + f"/node_{ndx}")
            shutil.copytree(str(src_dir) + "/nimbus-keys", str(node_dir) + "/keys")
            shutil.copytree(str(src_dir) + "/secrets", str(node_dir) + "/secrets")
        # done now clean up..
        shutil.rmtree(str(self.testnet_dir) + "/validators/")

        # just in case set a deposit deploy block.
        with open(f"{str(self.testnet_dir)}/deposit_contract_block.txt", "w") as f:
            f.write(
                "0"
            )

class LodestarTestnetGenerator(ConsensusDirectoryGenerator):
    def __init__(self, consensus_client):
        super().__init__(consensus_client)

    def finalize_testnet_dir(self):
        """
        Copy validator info into local client.
        """
        for ndx in range(self.client_module.get("num-nodes")):
            node_dir = pathlib.Path(str(self.testnet_dir) + f"/node_{ndx}")
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