"""
Testnet Bootstrapper is responsible for bootstrapping a testnet from an etb-config file.
"""
import argparse
import json
import logging
import os
import pathlib
import random
import re
import shutil
import time
from pathlib import Path
from typing import Union, Any

import requests
from ruamel import yaml

from etb.common.utils import create_logger
from etb.config.etb_config import (
    ETBConfig,
    FilesConfig,
    ClientInstance,
    ClientInstanceCollectionConfig,
)
from etb.genesis.consensus_genesis import ConsensusGenesisWriter
from etb.genesis.execution_genesis import ExecutionGenesisWriter
from etb.interfaces.client_request import (
    eth_getBlockByNumber,
    admin_nodeInfo,
    perform_batched_request,
    admin_addPeer,
)
from etb.interfaces.external.eth2_val_tools import Eth2ValTools


class EthereumTestnetBootstrapper:
    """The Testnet Bootstrapper wraps all the consensus and execution
    bootstrapper logic to bootstrap all the clients. It also handles the
    consensus bootnode.

    The EthereumTestnetBootstrapper is used to init the testnet and later is
    used to bootstrap and run the testnet.

    Bootstrapper responsible for:
        - clean: try to remove the files from a previous run
                        (This is run on make clean)
        - init-testnet: create the directory structure for the testnet and
                        populate it with the static-files.
                        (This is run on make init-testnet)
        - bootstrap-testnet: run the consensus and execution bootstrappers
                        which will start up the testnet.
                        (This is run on docker-compose up)
    """

    def __init__(self):
        pass

    def clean(self):
        """Cleans up the testnet root directory and docker-compose file.

        @return:
        """
        files_config = FilesConfig()
        logging.info(
            f"Cleaning up the testnet directories: {files_config.testnet_root}"
        )
        docker_compose_file = files_config.docker_compose_file
        if files_config.testnet_root.exists():
            for root, dirs, files in os.walk(files_config.testnet_root):
                for file in files:
                    pathlib.Path(f"{root}/{file}").unlink()
                for directory in dirs:
                    shutil.rmtree(f"{root}/{directory}")

        if docker_compose_file.exists():
            docker_compose_file.unlink()

    def init_testnet(self, config_path: Path):
        """Initializes the testnet directory, 3 phases.

        1. populate client-specific static files:
            - client-directories
            - jwt-secret files
            - validator keystores
        2. Write the etb-config file into the testnet-dir.
        3. Write the docker-compose file to use for bootstrapping later.
        @param config_path: path to the etb-config file.
        @return:
        """
        etb_config: ETBConfig = ETBConfig(config_path)
        # this file holds all the static files for the nodes.
        local_testnet_dir: pathlib.Path = etb_config.files.local_testnet_dir

        # check to see if we have a testnet already here.
        if local_testnet_dir.exists():
            raise Exception(
                f"non-empty local-testnet-dir:{local_testnet_dir}, please run `make clean` first."
            )
        local_testnet_dir.mkdir(parents=True)  # /data/local_testnet

        # create the client directories
        # directory structure:
        # /testnet_root/local_testnet/collection_name/node_<node_num>/{cl
        # files/el dir}
        logging.info("populating client directories and jwt-secret files")
        client_instance: ClientInstance
        for client_instance in etb_config.get_client_instances():
            client_instance.el_dir.mkdir(parents=True, exist_ok=True)

            # create the jwt-secret file:
            # /testnet_dir/collection_name/node_<node_num>/jwt-secret
            jwt_secret_file: pathlib.Path = client_instance.jwt_secret_file
            logging.debug(f"populating jwt-secret-file: {jwt_secret_file}")
            with open(jwt_secret_file, "w", encoding="utf-8") as jwt_file:
                jwt_file.write(f"0x{random.randbytes(32).hex()}")

        # write all validator keystores.
        logging.info("populating validator keystores")
        self._write_validator_keystores(etb_config)

        # write the etb-config file into the testnet-dir.
        logging.info("writing etb-config file..")
        etb_config.write_config(etb_config.files.testnet_root / "etb-config.yaml")

        # lastly write the docker-compose file to use for bootstrapping later.
        logging.info("writing docker-compose file..")
        with open(
            etb_config.files.docker_compose_file, "w", encoding="utf-8"
        ) as docker_file:
            # remove identities and aliases from the yaml file to ease
            # readability for end users.
            class NoAliasDumper(yaml.SafeDumper):
                """
                A dumper that will never emit aliases.
                """

                def ignore_aliases(self, data):
                    return True

            docker_file.write(
                yaml.dump(etb_config.get_docker_compose_repr(), Dumper=NoAliasDumper)
            )

    def bootstrap_testnet(self, config_path: Path, global_timeout: int = 60):
        """Bootstraps the testnet. This happens in several phases, each
        seperated by checkpoints.

        1. Set bootstrap dynamic entry and write the config file and checkpoint file.
        2. Signal the consensus bootnodes to come up.
        3. Start the execution clients.

        @param global_timeout: the max amount of time to wait for any RPC request.
        @param config_path: path to the etb-config file.
        @return:
        """

        # 1 prep the shared etb-config.yaml file with the bootstrap time.
        logging.info("bootstrapping testnet..")
        etb_config: ETBConfig = ETBConfig(path=config_path)
        etb_config.set_genesis_time(int(time.time()))
        etb_config.write_config(etb_config.files.testnet_root / "etb-config.yaml")
        with open(
            etb_config.files.etb_config_checkpoint_file, "w", encoding="utf-8"
        ) as etb_checkpoint:
            etb_checkpoint.write("")

        # (if you need anything to run before the testnet starts, do it here)

        # 2 signal the consensus bootnodes to come up.
        logging.info("signaling consensus bootnodes to come up..")
        with open(
            etb_config.files.consensus_bootnode_checkpoint_file, "w"
        ) as bootnode_checkpoint:
            bootnode_checkpoint.write("")

        # 3. handle execution clients.
        # create genesis files
        logging.info("creating execution layer genesis files..")
        egw = ExecutionGenesisWriter(etb_config)
        with open(
            etb_config.files.geth_genesis_file, "w", encoding="utf-8"
        ) as geth_genesis:
            geth_genesis.write(json.dumps(egw.create_geth_genesis()))
        with open(
            etb_config.files.besu_genesis_file, "w", encoding="utf-8"
        ) as besu_genesis:
            besu_genesis.write(json.dumps(egw.create_besu_genesis()))
        with open(
            etb_config.files.nether_mind_genesis_file, "w", encoding="utf-8"
        ) as nethermind_genesis:
            nethermind_genesis.write(json.dumps(egw.create_nethermind_genesis()))
        # signal all execution clients to start.
        with open(
            etb_config.files.execution_checkpoint_file, "w", encoding="utf-8"
        ) as execution_checkpoint:
            execution_checkpoint.write("")
        # now that the ELs are all up we manually pair them.
        self._pair_execution_clients(etb_config, global_timeout=global_timeout)

        # 4. get the consensus clients ready to come up.
        # create and write all the required files into the testnet root.
        block_hash, block_number = self.get_deposit_contract_deployment_block(
            etb_config, global_timeout=global_timeout
        )
        etb_block_hash_file: pathlib.Path = (
            etb_config.files.deposit_contract_deployment_block_hash_file
        )
        etb_block_number_file: pathlib.Path = (
            etb_config.files.deposit_contract_deployment_block_number_file
        )
        with open(etb_block_hash_file, "w", encoding="utf-8") as block_hash_file:
            block_hash_file.write(block_hash)
        with open(etb_block_number_file, "w", encoding="utf-8") as block_number_file:
            block_number_file.write(str(block_number))
        logging.info("Writing consensus genesis files")
        cgw = ConsensusGenesisWriter(etb_config)
        with open(
            etb_config.files.consensus_config_file, "w", encoding="utf-8"
        ) as consensus_config:
            consensus_config.write(cgw.create_consensus_config_yaml())
        with open(etb_config.files.consensus_genesis_file, "wb") as consensus_genesis:
            genesis_ssz = cgw.create_consensus_genesis_ssz()
            # got an exception, raise it. if not then we have bytes to write.
            if isinstance(genesis_ssz, Exception):
                raise genesis_ssz
            consensus_genesis.write(cgw.create_consensus_genesis_ssz())
        # now copy the files into their respective dirs.
        # note the nodes are using the top level dir instead of the node dir.
        config: ClientInstanceCollectionConfig
        for config in etb_config.client_collections:
            destination = config.collection_dir
            shutil.copy(etb_config.files.consensus_config_file, destination)
            shutil.copy(etb_config.files.consensus_genesis_file, destination)
            if config.consensus_config.client == "lighthouse":
                shutil.copy(etb_block_number_file, destination / "deploy_block.txt")
            if config.consensus_config.client == "nimbus":
                shutil.copy(
                    etb_block_hash_file, destination / "deposit_contract_block_hash.txt"
                )
                shutil.copy(
                    etb_block_number_file, destination / "deposit_contract_block.txt"
                )
        # signal the CL clients to start
        with open(
            etb_config.files.consensus_checkpoint_file, "w", encoding="utf-8"
        ) as consensus_checkpoint:
            consensus_checkpoint.write("")

        logging.info("testnet bootstrapped.")

    def create_keystores(self, config_path: Path):
        """This is not used in the bootstrapping process, but is useful for
        creating the keystores for validators.

        There is no need to call this method during normal operation.
        @param config_path: path of the etb-config.yaml file @return:
        """
        logging.warning("create_keystores called outside of bootstrapping process.")
        logging.warning(
            "This will not init a testnet or bootstrap one. See docs for more info."
        )
        self._write_validator_keystores(ETBConfig(config_path))

    def _pair_execution_clients(self, etb_config: ETBConfig, global_timeout: int):
        """Iterate through all client-instances which have the admin api.

        enabled and pair them. @param etb_config: config of
        experiment @return:
        """
        admin_api_filter: re.Pattern[str] = re.compile(r"(admin|ADMIN)")
        el_clients_to_pair: list[ClientInstance] = []
        # lots of retries as clients can take a while to start.
        # node_info_rpc_request = admin_nodeInfo(max_retries=20, timeout=global_timeout)

        client_instances = etb_config.get_client_instances()
        for instance in client_instances:
            if admin_api_filter.search(",".join(instance.execution_config.http_apis)):
                el_clients_to_pair.append(instance)
            else:
                logging.warning(
                    f"Execution client for {instance.name} does not support the admin API."
                )
                logging.info(
                    f"Skipping execution pairing for instance: {instance.name}"
                )

        enodes: dict[ClientInstance, str] = {}
        el_client: ClientInstance
        # it may take a while for the clients to come up; so retry a lot.
        rpc_request = admin_nodeInfo(max_retries=40, timeout=global_timeout)
        for el_client, rpc_future in perform_batched_request(
            rpc_request, el_clients_to_pair
        ).items():
            result: Union[requests.Response, Exception] = rpc_future.result()
            if rpc_request.is_valid(result):
                enodes[el_client] = rpc_request.get_enode(result)
            else:
                logging.error(
                    f"Failed to get enode from {el_client.name}, error: {result}"
                )
                # bail early
                raise result

        logging.debug(
            f"Fetched the following enodes: {enodes} from the execution clients."
        )

        # now peer the clients with everyone but themselves.
        for el_peer, enode in enodes.items():
            add_enode_rpc_request = admin_addPeer(enode=enode, timeout=global_timeout)
            for el_client in el_clients_to_pair:
                # don't pair clients with themselves.
                if el_client != el_peer:
                    logging.debug(f"adding peer {el_peer} to el_client {el_client}")
                    resp = add_enode_rpc_request.perform_request(el_client)
                    if not add_enode_rpc_request.is_valid(resp):
                        logging.error(f"admin_addPeer failed with {resp}")
                        # bail early
                        raise resp

    def _write_validator_keystores(self, etb_config: ETBConfig):
        """
        Populates the validator keystores for all the clients.
        keys are generated using eth2-val-tools and dropped in the node_dir:
            /testnet_root/local_testnet/collection_name/node_<node_num>/keystores/
        they are then moved up one dir and the keystore dir is removed.
        @param etb_config: ETBConfig
        @return:
        """

        eth2_val_tools = Eth2ValTools()
        mnemonic = etb_config.testnet_config.consensus_layer.validator_mnemonic
        logging.debug(f"using mnemonic:\n\t{mnemonic}")
        client_instance: ClientInstance
        for client_instance in etb_config.get_client_instances():
            cl_client = client_instance.consensus_config.client
            if cl_client not in ["prysm", "lighthouse", "teku", "nimbus", "lodestar"]:
                raise Exception(f"client: {cl_client} not supported for keystores")
            consensus_node_dir: pathlib.Path = client_instance.node_dir
            keystore_dir: pathlib.Path = consensus_node_dir / pathlib.Path("keystores/")
            vpn = client_instance.consensus_config.num_validators  # validators per node
            offset = client_instance.ndx * vpn
            min_ndx = client_instance.collection_config.validator_offset_start + offset
            max_ndx = min_ndx + vpn
            logging.debug(f"populating keystores for client: {client_instance.name}")
            logging.debug(f"min_ndx: {min_ndx}, max_ndx: {max_ndx}")
            if cl_client == "prysm":
                eth2_val_tools.generate_keystores(
                    out_path=keystore_dir,
                    min_ndx=min_ndx,
                    max_ndx=max_ndx,
                    mnemonic=mnemonic,
                    prysm=True,
                    prysm_password=client_instance.validator_password,
                )

                for item in pathlib.Path(keystore_dir).glob("prysm/*"):
                    if item.is_dir():
                        shutil.copytree(item, consensus_node_dir / item.name)
                    else:
                        shutil.copy(item, consensus_node_dir / item.name)
                # prysm requires a wallet-password.txt to launch.
                wallet_password_path: pathlib.Path = (
                    consensus_node_dir / "wallet-password.txt"
                )
                with open(wallet_password_path, "w") as wallet_password_file:
                    wallet_password_file.write(client_instance.validator_password)

            else:
                eth2_val_tools.generate_keystores(
                    out_path=keystore_dir,
                    min_ndx=min_ndx,
                    max_ndx=max_ndx,
                    mnemonic=mnemonic,
                )
                # these are the defaults shared by most of the clients
                keystore_src: pathlib.Path = (
                    keystore_dir / "keys"
                )  # where the generated keystores are
                keystore_dst: pathlib.Path = (
                    consensus_node_dir / "keys"
                )  # where the keystores will be moved to
                secret_src: pathlib.Path = (
                    keystore_dir / "secrets"
                )  # where the generated secrets are
                secret_dst: pathlib.Path = (
                    consensus_node_dir / "secrets"
                )  # where the secrets will be moved to
                if cl_client == "teku":
                    keystore_src = keystore_dir / "teku-keys"
                    secret_src = keystore_dir / "teku-secrets"
                elif cl_client == "nimbus":
                    keystore_src = keystore_dir / "nimbus-keys"
                elif cl_client == "lodestar":
                    secret_src = keystore_dir / "lodestar-secrets"
                    # go ahead and create the validatordb dir for lodestar
                    pathlib.Path(consensus_node_dir / "validatordb").mkdir()
                # copy everything over
                shutil.copytree(keystore_src, keystore_dst)
                shutil.copytree(secret_src, secret_dst)
            # finished, remove the generated keystores.
            shutil.rmtree(keystore_dir)

    def get_deposit_contract_deployment_block(
        self, etb_config: ETBConfig, global_timeout: int
    ) -> tuple[str, int]:
        """Fetch a random EL client that implements the eth http api and get
        the 0th block for the contract deployment.

        :return: (block_hash, block_number)
        """
        el_eth_regex = re.compile(r"(eth|ETH)")
        plausible_instances: list[ClientInstance] = []
        for instance in etb_config.get_client_instances():
            if el_eth_regex.search(",".join(instance.execution_config.http_apis)):
                plausible_instances.append(instance)

        if len(plausible_instances) == 0:
            raise Exception("No clients have an EL that supports the eth http-api")

        target_instance = random.choice(plausible_instances)
        logging.debug(
            f"Using instance: {target_instance.name} to get the contract deployment block."
        )
        # contract deployed at genesis
        get_block_rpc_request = eth_getBlockByNumber("0x0", timeout=global_timeout)
        resp = get_block_rpc_request.perform_request(target_instance)
        if not get_block_rpc_request.is_valid(resp):
            resp: Exception  # resp is an exception
            raise Exception(
                f"Failed to get block 0 from {target_instance.name}: {str(resp)}"
            )

        block: dict[str, Any] = get_block_rpc_request.get_block(resp)
        block_number = block["number"]
        block_hash = block["hash"]
        logging.debug(f"Got block {block_number} with hash: {block_hash}")
        return block_hash, int(block_number, 16)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        dest="config",
        required=False,
        help="Which config file to use to create a testnet.",
    )

    parser.add_argument(
        "--clean",
        dest="clean",
        action="store_true",
        default=False,
        help="Clear the last run.",
    )

    parser.add_argument(
        "--init-testnet",
        dest="init_testnet",
        action="store_true",
        default=False,
        help="Initialize the testnet to be bootstrapped.",
    )

    parser.add_argument(
        "--bootstrap-testnet",
        dest="bootstrap_testnet",
        action="store_true",
        default=False,
        help="Start the testnet",
    )

    parser.add_argument(
        "--log-level",
        dest="log_level",
        default="debug",
        help="logging level to use.",
    )

    args = parser.parse_args()

    create_logger(
        log_level=args.log_level, name="testnet_bootstrapper", log_to_file=True
    )
    logging.info("testnet_bootstrapper has started.")

    etb = EthereumTestnetBootstrapper()

    if args.clean:
        etb.clean()
        logging.debug("testnet_bootstrapper has finished cleaning up.")

    if args.init_testnet:
        # make sure we are going from source.
        if args.config.split("/")[0] != "source":
            logging.debug(
                "prepending source to the config path in order to map in the config file."
            )
            path_to_config = pathlib.Path(f"source/{args.config}")
        else:
            path_to_config = pathlib.Path(args.config)

        etb.init_testnet(path_to_config)
        logging.debug("testnet_bootstrapper has finished init-ing the testnet.")

    if args.bootstrap_testnet:
        # the config path lies in /source/data/etb-config.yaml
        path_to_config = pathlib.Path("source/data/etb-config.yaml")
        etb.bootstrap_testnet(path_to_config)
        logging.debug("testnet_bootstrapper has finished bootstrapping the testnet.")
