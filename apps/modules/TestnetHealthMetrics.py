"""
    Wrappers around various API's to allow the user to easily write modules to
    query various metrics.
"""
from .BeaconAPI import ETBConsensusBeaconAPI, APIRequest
from .ExecutionRPC import ETBExecutionRPC, RPCMethod

from enum import Enum
import logging
import time


class TestnetHealthMetric(object):
    def __init__(self, request_obj, metric_name):
        self.metric_name = metric_name
        self.request_obj = request_obj
        # repr string can be used for modules that just want to log metrics
        self.repr_string = None
        # result contains raw info for other modules to use for calculations
        self.result = None
        self.last_run = None

    def __repr__(self):
        if self.last_run is None:
            return f"{self.metric_name} : No result (not run)"
        else:
            return f"{self.metric_name} : {self.last_run} : {self.repr_string}"

    def perform_and_log(self, etb_api):
        self.last_run = time.time()
        self.result = self._perform_method(etb_api)
        self.repr_string = self._unpack_results(etb_api)

    def _perform_method(self, etb_api):
        raise Exception("_perform_method must be overridden")

    def _unpack_results(self, etb_api):
        raise Exception("_unpack_results must be overridden")


class GetUniqueHeads(TestnetHealthMetric):
    def __init__(self):
        api_request = APIRequest("/eth/v2/beacon/blocks/head")
        super().__init__(api_request, "unique-consensus-heads")

    # for modules that want to see if there is a fork, or process the data.
    def _perform_method(self, etb_api):
        if not isinstance(etb_api, ETBConsensusBeaconAPI):
            raise Exception("Wrong ETB_API")

        all_responses = {}
        for name, response in etb_api.do_api_request(
            self.request_obj, all_clients=True
        ).items():
            if response is not None:
                slot = response.json()["data"]["message"]["slot"]
                state_root = response.json()["data"]["message"]["state_root"]
                all_responses[name] = (slot, state_root)

        return all_responses

    def _unpack_results(self, etb_api):
        unique_resps = {}

        for name, response in self.result.items():
            if response in unique_resps:
                unique_resps[response].append(name)
            else:
                unique_resps[response] = [name]

        num_heads = len(unique_resps.keys())
        if num_heads != 1:
            repr_string = f"WARN: found {num_heads} forks: {unique_resps}"
        else:
            slot, state_root = list(unique_resps.keys())[0]
            repr_string = f"Consensus {slot}:{state_root}"

        return repr_string


class TestnetHealthAPI(object):
    def __init__(self, etb_config):
        self.etb_config = etb_config
        self.beacon_api = ETBConsensusBeaconAPI(etb_config)
        self.execution_rpc = ETBExecutionRPC(etb_config)

        self.metrics = {}

    def __repr__(self):
        out = ""
        for metric_name, metric in self.metrics.items():
            out += metric_name + "\n"
            out += "\t" + metric.__repr__()

        return out

    def add_metric(self, thm, name=None):
        if name is None:
            self.metrics[thm.metric_name] = thm
        else:
            self.metrics[name] = thm

    def perform_metric(self, name):
        try:
            metric = self.metrics[name]
            if isinstance(metric.request_obj, APIRequest):
                metric.perform_and_log(self.beacon_api)
            elif isinstance(metric.request_obj, RPCMethod):
                metric.perform_and_log(self.execution_rpc)
            else:
                raise Exception(f"Bad request_obj: {type(metric.request_obj)}")

            return metric.result

        except IndexError:
            logging.error("TestnetHealthAPI:perform index error {name}")
            return None

        except Exception as e:
            raise e

    def perform_all_metrics(self):
        all_results = {}
        for metric_name, metric in self.metrics.items():
            self.perform_metric(metric_name)
            all_results[metric_name] = metric.result

        return all_results
