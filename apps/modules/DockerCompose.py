import logging
import re

from ruamel import yaml

from .ETBConfig import (ConsensusClient, ETBConfig, ExecutionClient,
                        GenericClient)

logger = logging.getLogger("bootstrapper_log")


class ClientWriter(object):
    def __init__(self, base_name, generic_client, curr_node):
        self.name = f"{base_name}-{curr_node}"
        self.client = generic_client
        self.curr_node = curr_node

        # global config
        self.etb_config = self.client.etb_config
        # execution config
        self.execution_config = self.client.execution_config
        # consensus config
        self.consensus_config = self.client.consensus_config
        # consensus bootnode configs
        self.consensus_bootnode_config = self.client.consensus_bootnode_config

        self.base_consensus_env_vars = [
            "preset-base",
            "genesis-fork-name",
            "end-fork-name",
            "testnet-dir",
            "node-dir",
            "ip-addr",
            "consensus-p2p-port",
            "beacon-api-port",
            "graffiti",
            "netrestrict-range",
            "beacon-metric-port",
            "beacon-rpc-port",
            "validator-rpc-port",
            "validator-metric-port",
            "execution-launcher",
            "local-execution-client",
            "consensus-target-peers",
            "consensus-bootnode-enr-file",
            "consensus-checkpoint-file",
            "ws-web3-ip-addr",
            "http-web3-ip-addr",
            "execution-bootnode",
        ]

        self.base_execution_env_vars = [
            "ip-addr",
            "execution-data-dir",
            "execution-p2p-port",
            "execution-http-port",
            "execution-ws-port",
            "http-apis",
            "ws-apis",
            "terminal-total-difficulty",
            "chain-id",
            "network-id",
            "netrestrict-range",
            "geth-genesis-file",
            "besu-genesis-file",
            "nether-mind-genesis-file",
            "end-fork-name",
            "execution-checkpoint-file",
            "execution-log-level",
        ]

        self.base_consensus_bootnode_env_vars = [
            "consensus-bootnode-checkpoint-file",
            "ip-addr",
            "consensus-bootnode-private-key",
            "consensus-bootnode-enr-port",
            "consensus-bootnode-api-port",
            "consensus-bootnode-enr-file",
        ]

        self.optional_consensus_vars = ["jwt-secret-file"]

        self.optional_execution_vars = [
            "jwt-secret-file",
            "execution-engine-port",  # no auth both http/ws are the same.
            "execution-engine-http-port",
            "execution-engine-ws-port",
            "execution-bootnode-private-key",
        ]

    def _get_docker_entrypoint(self):
        if isinstance(self.client.get("entrypoint"), str):
            return self.client.get("entrypoint").split()

        else:
            return self.client.get("entrypoint")

    def _get_docker_networks(self):
        if self.client.has("network-name"):
            network_name = self.client.get("network-name")
        else:
            network_name = self.etb_config.get("network-name")

        network = {"ipv4_address": self.client.get("ip-addr", self.curr_node)}
        return {network_name: network}

    def _get_docker_image(self):
        return f'{self.client.get("image")}:{self.client.get("tag")}'

    def _get_docker_container_name(self):
        return f'{self.client.get("container-name")}-{self.curr_node}'

    def _get_docker_volumes(self):
        if self.client.has("volumes"):
            volumes = self.client.get("volumes")
        else:
            volumes = [str(x) for x in self.etb_config.get("volumes")]

        return volumes

    def _get_docker_service_entry(self):

        return {
            "container_name": self._get_docker_container_name(),
            "image": self._get_docker_image(),
            "networks": self._get_docker_networks(),
            "entrypoint": self._get_docker_entrypoint(),
            "environment": self._get_docker_env(),
            "volumes": self._get_docker_volumes(),
        }

    def _get_env_var(self, var):
        """
        Iterate in the following order to find the correct attr(). We do it
        in this order to allow various portions of the config to overwrite
        others.
        """
        # getter = f'get_{var.replace("-","_")}'
        value = None
        is_set = False
        if self.etb_config.has(var):
            value = self.etb_config.get(var)
            is_set = True

        if self.client.has(var):
            value = self.client.get(var, self.curr_node)
            is_set = True

        if value is None and is_set is True:
            value = ""
        if value is None and is_set is False:
            raise Exception(f"Failed to set value: {var}")
        return value

    def _get_docker_env(self):
        env_vars = {}
        # additional env's overwrite everything.
        # we do execution and then consensus to allow overwriting the ecc
        # for example the execution_data_dir a consensus client should place
        # it in the node dir.
        if self.execution_config is not None:
            for k in self.base_execution_env_vars:
                var = f'{k.upper().replace("-","_")}'
                env_vars[var] = self._get_env_var(k)

            for k in self.optional_execution_vars:
                if self.client.has(k):
                    var = f'{k.upper().replace("-","_")}'
                    env_vars[var] = self._get_env_var(k)

        if self.consensus_config is not None:
            for k in self.base_consensus_env_vars:
                var = f'{k.upper().replace("-","_")}'
                env_vars[var] = self._get_env_var(k)

            for k in self.optional_consensus_vars:
                if self.client.has(k):
                    var = f'{k.upper().replace("-","_")}'
                    env_vars[var] = self._get_env_var(k)

        if self.consensus_bootnode_config is not None:
            for k in self.base_consensus_bootnode_env_vars:
                var = f'{k.upper().replace("-","_")}'
                env_vars[var] = self._get_env_var(k)

        if self.client.has("additional-env"):
            for k, v in self.client.get("additional-env").items():
                var = f'{k.upper().replace("-","_")}'
                env_vars[var] = v

        return env_vars


class DockerComposeWriter(object):
    def __init__(self, etb_config):
        self.config = etb_config
        self.yaml = self._base()

    def _base(self):
        return {
            "services": {},
            "networks": {
                self.config.get("network-name"): {
                    "driver": "bridge",
                    "ipam": {"config": [{"subnet": self.config.get("ip-subnet")}]},
                }
            },
        }

    def add_services(self):

        for name, cc in self.config.get_consensus_clients().items():
            for n in range(cc.get("num-nodes")):
                logger.info(f"Dockerizing-{name} consensus-client.")
                cw = ClientWriter(name, cc, n)
                self.yaml["services"][cw.name] = cw._get_docker_service_entry()
        for (
            name,
            ec,
        ) in self.config.get_execution_clients().items():
            for n in range(ec.get("num-nodes")):
                logger.info(f"Dockerizing-{name} execution-client.")
                cw = ClientWriter(name, ec, n)
                self.yaml["services"][cw.name] = cw._get_docker_service_entry()

        for name, gc in self.config.get_generic_modules().items():
            for n in range(gc.get("num-nodes")):
                logger.info(f"Dockerizing-{name} generic-module-client.")
                cw = ClientWriter(name, gc, n)
                self.yaml["services"][cw.name] = cw._get_docker_service_entry()

        for name, cb in self.config.get_consensus_bootnodes().items():
            for n in range(cb.get("num-nodes")):
                logger.info(f"Dockerizing-{name} consensus-bootnode-client.")
                cw = ClientWriter(name, cb, n)
                self.yaml["services"][cw.name] = cw._get_docker_service_entry()

        # do the testnet bootstrapper.
        for name, tb in self.config.get_testnet_bootstrapper().items():
            cw = ClientWriter(name, tb, 0)
            self.yaml["services"][cw.name] = cw._get_docker_service_entry()


def generate_docker_compose(global_config):
    dcw = DockerComposeWriter(global_config)
    dcw.add_services()
    return dcw.yaml
