"""
    The ConsensusHealthMonitor continually monitors the health of the consensus layer.
    It has to tracks on both a per-client basis and a consensus layer basis.
    The consensus-layer basis keeps track of the following:
        current heads
        missed slots
    The per-client metrics are on an
        peerId
        peers
        duties

"""
from .BeaconAPI import BeaconClientAPI, BeaconGetBlock
import subprocess


class ConsensusClientMonitor(object):
    """
    stores a consensus client.

    Attributes:
        (static):
            name
            ip_address
            node_dir
            TODO: validator_keys
        (objects):
            BeaconAPI

    The client monitor stores the following:
        self.duties {epoch: {validator : duties}}
        self.slots {epoch: {slot in epoch : state_root}}
    """

    def __init__(self, etb_config, cc, node, timeout=1, retry_delay=1):
        self.etb_config = etb_config
        self.client = cc
        self.ip = cc.get("ip-addr", node)
        self.api_port = cc.get("beacon-api-port")
        self.node_dir = cc.get("node-dir", node)
        self.beacon_api = BeaconClientAPI(
            f"http://{self.ip}:{self.api_port}",
            non_error=True,
            timeout=timeout,
            retry_delay=retry_delay,
        )

        self.curr_slot = 0
        self.curr_epoch = 0
        self.curr_block = None

        self.slots = {}
        self.blocks = {}
        self.duties = {}

    def _slot_to_epoch_offest(self, slot):
        return slot // 32, slot % 32

    def get_local_head(self):
        epoch, slot = self._slot_to_epoch_offest(self.curr_slot)
        return self.slots[epoch][slot]

    def get_block(self, block):
        request = BeaconGetBlock(block)
        response = self.beacon_api.get_api_response(request)
        if response.status_code == 200:
            return response.json()
        return None

    def get_slot_from_block(self, block):
        return int(block["data"]["message"]["slot"])

    def add_block(self, block, slot):
        block_epoch, block_slot = self._slot_to_epoch_offest(slot)
        if block_epoch not in self.blocks:
            self.blocks[block_epoch] = {}
        self.blocks[block_epoch][block_slot] = block

    def get_missed_slots(self):
        missed_slots = {}
        for epoch, slots in self.blocks.items():
            missed_slots[epoch] = []
            for slot, block in slots.items():
                if block is None:
                    missed_slots[epoch].append(slot)

    def update(self):
        newest_block = self.get_block("head")
        if newest_block is not None:
            slot = self.get_slot_from_block(newest_block)
            if slot > self.curr_slot:
                for x in range(self.curr_slot, slot):
                    block = self.get_block(x)
                    self.add_block(block, x)
                self.curr_slot = slot
                self.curr_epoch = slot // 32
                self.curr_block = block


class ConsensusHealthMonitor(object):
    def __init__(self, etb_config, timeout=1, retry_delay=1):
        self.etb_config = etb_config
        self.timeout = timeout
        self.retry_delay = retry_delay

        self.cc_monitors = {}

        self._populate_consensus_clients()

        self.proposer_duties = {}
        self.validator_client_map = {}

    def _populate_consensus_clients(self):
        for name, cc in self.etb_config.get("consensus-clients").items():
            for node in range(cc.get("num-nodes")):
                node_name = f"{name}-{node}"
                self.cc_monitors[node_name] = ConsensusClientMonitor(
                    self,
                    cc,
                    node,
                    timeout=self.timeout,
                    retry_delay=self.retry_delay,
                )

    def _get_validator_pubkey_range(self, start, stop):
        mnemonic = self.etb_config.get("validator-mnemonic")
        cmd = [
            "eth2-val-tools",
            "pubkeys",
            "--source-min",
            f"{start}",
            "--source-max",
            f"{stop}",
            "--validators-mnemonic",
            f"{mnemonic}",
        ]
        output = subprocess.run(cmd, capture_output=True)
        return output.stdout.decode("utf-8").split("\n")[:-1]

    def _get_client_pubkey_map(self):
        for name, cc in self.etb_config.get("consensus-clients").items():
            for node in range(cc.get("num-nodes")):
                validator_start = cc.get("validator-offset-start", node)
                validator_stop = validator_start + cc.get("num-validators")
                node_name = f"{name}-{node}"
                for validator_pubkey in self._get_validator_pubkey_range(
                    validator_start, validator_stop
                ):
                    self.validator_client_map[validator_pubkey] = node_name

    def update_monitors(self):
        for name, monitor in self.cc_monitors.items():
            monitor.update()
