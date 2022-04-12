import requests
import time
import sys
from ruamel import yaml

available_api_requests = {
    "beacon": [
        "/eth/v1/beacon/genesis",
        "/eth/v1/beacon/blocks",
        "/eth/v1/beacon/pool/attestations",
        "/eth/v1/beacon/pool/attester_slashings",
        "/eth/v1/beacon/pool/proposer_slashings",
        "/eth/v1/beacon/pool/voluntary_exits",
    ],
}


class APIResponse(object):
    def __init__(self, response):
        self.response = response
        self.status_code = response.status_code if response else 500
        if self.status_code == 200:
            self.data = response.json()["data"]
        else:
            self.data = None

    def __repr__(self):
        return f"{self.status_code} : {self.data}"


class APIRequest(object):
    def __init__(self, path, timeout=5, retries=30, retry_delay=15):
        self.path = path
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay

    def __repr__(self):
        return f"{self.path}"

    def get_response(self, api_client):
        return APIResponse(self._get_with_retry(api_client.host, api_client.port))

    def _get_with_retry(self, host, port):
        url = f"http://{host}:{port}{self.path}"
        print(f"Attempting {url}", flush=True)
        attempt = 1
        last_response = None
        while attempt <= self.retries:
            status_code = 500
            try:
                last_response = requests.get(url, timeout=self.timeout)
                status_code = last_response.status_code
                # print(f"status_code={status_code}; response={last_response.json()}", flush=True)
            except requests.exceptions.RequestException as e:
                print(e, file=sys.stderr, flush=True)
            if status_code != 200:
                print(
                    f"\tattempt={attempt}/{self.retries}; delay={self.retry_delay}s",
                    flush=True,
                )
                time.sleep(self.retry_delay)
                attempt += 1
            else:
                break
        return last_response


class BeaconAPIManager(object):
    def __init__(self):
        self.clients = {}
        # apis to access for status

    def __repr__(self):
        out = ""
        for v in self.clients.values():
            out += v.__repr__() + "\n"
        return out

    def add_client(self, client):
        self.clients[client.host] = client


class BeaconAPIClient(object):
    def __init__(self, host, port, client):
        self.host = host
        self.port = port
        self.client = client

    def __repr__(self):
        return f"{self.host}:{self.port} ({self.client})"

    def get_genesis(self):
        response = self._get_with_retry(
            f"http://{self.host}:{self.port}/eth/v1/beacon/genesis",
        )
        if response is not None and response.status_code == 200:
            genesis_time = int(response.json()["data"]["genesis_time"])
        else:
            raise Exception("Failed to get genesis")
        return genesis_time

    def get_block_header(self, block_number, timeout=5, retries=30, retry_delay=15):
        api_request = APIRequest(
            f"/eth/v1/beacon/headers/{block_number}", timeout, retries, retry_delay
        )
        return api_request.get_response(self)

    def get_head_block_header(self):
        return self.get_block_header("head")

    def get_block_roots(self, max_block=None, version=2):
        """
        Find the current block_header and
        extract all roots in the list from 0 to that number.
        """
        if max_block is None:
            block_header = self.get_head_block_header()
            slot = block_header.data["header"]["message"]["slot"]

        else:
            slot = max_block

        blocks = []

        for i in range(int(slot)):
            blocks.append(self.get_block_header(i, timeout=1, retries=1, retry_delay=1))

        return blocks


def get_api_manager_from_config(path):
    manager = BeaconAPIManager()
    with open(path, "r") as f:
        data = yaml.safe_load(f.read())

    for client_module in data["consensus-clients"]:
        client_config = data["consensus-clients"][client_module]
        consensus_config = data["consensus-configs"][client_config["consensus-config"]]
        client_name = client_config["client-name"]
        ip_segments = client_config["start-ip-addr"].split(".")
        prefix = ".".join(ip_segments[:3]) + "."
        base = int(ip_segments[-1])

        for ndx in range(consensus_config["num-nodes"]):
            ip = prefix + str(base + ndx)
            port = consensus_config["start-beacon-api-port"] + ndx
            api_client = BeaconAPIClient(ip, port, client_name)
            manager.add_client(api_client)
    return manager
