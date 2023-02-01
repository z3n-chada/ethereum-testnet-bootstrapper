import time
from concurrent.futures import ThreadPoolExecutor

import requests

"""
    General overview for rpc/api is of the following.

    1 object represents the request. it should have a local timeout.
        objects can inherit from this for commononly used requests.

    1 object represents a single endpoint connection for sending transactions.
        this should have the retries/non-error/global timeout to use.
        it sends the requests does some checks and returns the value that
        conforms or the last value retreived in the case of global/timeout
        or retry limit.

    1 object that wraps the etb_config to allow you to easily work with it.
        should allow you to choose which clients you wish to interact with.
"""


class APIRequest(object):
    def __init__(self, path, timeout=5):
        self.path = path
        self.timeout = timeout
        self.error = None  # defined by inheritance.
        # self.retries = retries
        # self.retry_delay = retry_delay

    def get_response(self, base_url):
        start = int(time.time())
        to = self.timeout
        while time.time() - start < to:
            try:
                return requests.get(f"{base_url}{self.path}", timeout=to)

            except requests.ConnectionError:
                # odds are the bootstrapper is trying to connect to a client
                # that is not up already.
                pass
            except requests.Timeout as e:
                # actually timed out.
                # return None but print the issue until we log.
                print(f"Request timed out {base_url}{self.path}")
                pass


class BeaconGetBlock(APIRequest):
    def __init__(self, block, timeout=5):
        super().__init__(f"/eth/v2/beacon/blocks/{block}", timeout=timeout)

class GetValidators(APIRequest):
    def __init__(self, timeout=5):
        super().__init__(f"/eth/v1/beacon/states/head/validators", timeout=timeout)

class GetFork(APIRequest):
    def __init__(self, state="head", timeout=5):
        super().__init__(f"/eth/v1/beacon/states/{state}/fork", timeout=timeout)

class GetGenesis(APIRequest):
    def __init__(self, timeout=5):
        super().__init__('/eth/v1/beacon/genesis', timeout=timeout)
"""
    Some useful APIs that get used regularly
"""


def _threadpool_executor_api_request_proxy(bucket, api, request):
    # threadpool executor to do things in parallel.
    return bucket, api.get_api_response(request)


class BeaconAPI(object):
    """
    Facilitates the comm chanel between one consensus client and ourselves.

    Sends the desired request and allows us to filter for error codes and
    timeout issues.
    """

    def __init__(self, base_url, non_error=True, timeout=5, retry_delay=1):
        self.base_url = base_url
        self.non_error = non_error
        self.timeout = timeout
        self.retry_delay = retry_delay

    def get_api_response(self, api_request):
        start = int(time.time())
        while time.time() - start < self.timeout:
            response = api_request.get_response(self.base_url)
            if response is not None:
                if response.status_code == 200:
                    return response
                else:
                    print(
                        f"{self.base_url}{api_request.path} got error status code {response.status_code}"
                    )
                    print("retrying...")
            time.sleep(self.retry_delay)
        return response


class ETBConsensusBeaconAPI(object):
    def __init__(self, etb_config, non_error=True, timeout=5, retry_delay=4):
        self.etb_config = etb_config
        self.timeout = timeout
        self.retry_delay = retry_delay
        self.non_error = non_error
        self.client_nodes = {}

        for name, api_path in self.etb_config.get_all_consensus_client_beacon_api_paths().items():
            self.client_nodes[name] = BeaconAPI(
                api_path,
                non_error=self.non_error,
                timeout=self.timeout,
                retry_delay=self.retry_delay
            )

    def get_client_nodes(self):
        return self.client_nodes.keys()

    def do_api_request(self, api_request, client_nodes=None, all_clients=False):
        if all_clients:
            ep = self.get_client_nodes()
        else:
            if not isinstance(client_nodes, list):
                ep = [client_nodes]
            else:
                ep = client_nodes

            # check that they are actually clients
            for cn in ep:
                if cn not in self.client_nodes.keys():
                    err = f"Invalid client node supplied: {cn}"
                    err += f" must be in {self.get_client_nodes()}"
                    raise Exception(err)

        all_responses = {}
        threadpool_endpoints = [self.client_nodes[name] for name in ep]
        threadpool_buckets = [name for name in ep]
        # execute the tasks with a concurrent threadpool executor.
        with ThreadPoolExecutor(max_workers=len(ep)) as executor:
            results = executor.map(
                _threadpool_executor_api_request_proxy,
                threadpool_buckets,
                threadpool_endpoints,
                [api_request for x in range(len(threadpool_endpoints))],
            )

        for bucket_response_tuple in list(results):
            client = bucket_response_tuple[0]
            response = bucket_response_tuple[1]
            all_responses[client] = response

        return all_responses
