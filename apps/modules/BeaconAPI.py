import requests
import time
import sys
from ruamel import yaml


class APIRequest(object):
    def __init__(self, path, timeout=5, retries=5, retry_delay=2):
        self.path = path
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay

    def get_response(self, base_url):
        response = requests.get(f"{base_url}{self.path}", timeout=self.timeout)
        return response

    def get_non_error_response(self, base_url):
        for x in range(self.retries):
            response = self.get_response(base_url)
            if response.status_code == 200:
                return response
            else:
                print(
                    f"{base_url}{self.path} got error status code {response.status_code}"
                )
                print("retrying..")
                time.sleep(self.retry_delay)
        return response


class BeaconAPI(object):
    def __init__(self, base_url, non_error=True):
        self.base_url = base_url
        self.non_error = non_error

    def get_api_response(self, api_request, non_error=True):
        if non_error:
            response = api_request.get_non_error_response(self.base_url)
        else:
            response = api_request.get_response(self.base_url)
        return response


class ETBConsensusBeaconAPI(object):
    def __init__(self, etb_config, non_error=True):
        self.etb_config = etb_config
        self._get_client_beacon_apis()
        self.non_error = non_error

    def _get_client_beacon_apis(self):
        self.beacon_apis = {}
        for name, cc in self.etb_config.get("consensus-clients").items():
            for node in range(cc.get("num-nodes")):
                ip = cc.get("ip-addr", node)
                port = cc.get("beacon-api-port")
                self.beacon_apis[f"{name}-{node}"] = BeaconAPI(f"http://{ip}:{port}")

    def do_api_request(self, api_request):
        responses = {}
        for name, beacon_api in self.beacon_apis.items():
            responses[name] = beacon_api.get_api_response(api_request, self.non_error)

        return responses


if __name__ == "__main__":

    etb_beacon_api = ETBConsensusBeaconAPI(config)
    api_requst = APIRequest("/eth/v2/beacon/blocks/head")
    for name, response in etb_beacon_api.do_api_request(api_request).items():
        print(f"{name}:{dir(response)}")
# class APIRequest(object):
#     def __init__(self, path, timeout=5, retries=30, retry_delay=15):
#         self.path = path
#         self.timeout = timeout
#         self.retries = retries
#         self.retry_delay = retry_delay
#
#     def __repr__(self):
#         return f"{self.path}"
#
#     def get_response(self, api_client):
#         return APIResponse(self._get_with_retry(api_client.host, api_client.port))
#
#     def _get_with_retry(self, host, port):
#         url = f"http://{host}:{port}{self.path}"
#         print(f"Attempting {url}", flush=True)
#         attempt = 1
#         last_response = None
#         while attempt <= self.retries:
#             status_code = 500
#             try:
#                 last_response = requests.get(url, timeout=self.timeout)
#                 status_code = last_response.status_code
#                 # print(f"status_code={status_code}; response={last_response.json()}", flush=True)
#             except requests.exceptions.RequestException as e:
#                 print(e, file=sys.stderr, flush=True)
#             if status_code != 200:
#                 print(
#                     f"\tattempt={attempt}/{self.retries}; delay={self.retry_delay}s",
#                     flush=True,
#                 )
#                 time.sleep(self.retry_delay)
#                 attempt += 1
#             else:
#                 break
#         return last_response
#
#
# class BeaconAPIEndpoint(object):
#     def __init__(self, url, retries=5, retry_delay=2):
#         self.url = url
#         self.retries = retries
#         self.retry_delay = retry_delay
#
#
#     def get_v2_beacon_block(self, blk="head"):
#         request = APIRequest(f'/eth/v2/beacon/blocks/{blk}', timeout=timeout, retries=self.retries, retry_delay=self.retry_delay)
#
#
# class GenericClientBeaconAPI(object):
#     def __init__(self, consensus_client):
#         if not isinstance(consensus_client, ConsensusClient):
#             # so far...
#             raise Exception("Only consensus clients have a consensus client")
#         self.client = consensus_client
#         if self.client.consensus_config is None:
#             raise Exception("Client has no consensus-config")
#         for n in range(self.client.get('num-nodes')):
#             ae =
