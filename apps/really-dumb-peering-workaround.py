from modules.ExecutionRPC import ExecutionClientJsonRPC
import time
import re
from ruamel import yaml
import json

if __name__ == "__main__":
    with open("docker-compose.yaml", "r") as f:
        data = yaml.safe_load(f.read())

    enodes = []
    results = []
    for service in data["services"]:
        if "environment" in data["services"][service]:
            env_vars = json.dumps(data["services"][service]["environment"])
            if "EXECUTION_HTTP_PORT" in env_vars and "IP_ADDR" in env_vars:
                print(env_vars)
                ip_regex = r"\"IP_ADDR=(?P<ip>([0-9]+\.){3}[0-9]+)\""
                execution_port_regex = r"EXECUTION_HTTP_PORT=(?P<port>[0-9]+)"
                ip_results = re.search(ip_regex, env_vars)
                port_results = re.search(execution_port_regex, env_vars)
                if ip_results is not None and port_results is not None:
                    ip = ip_results.group("ip")
                    port = port_results.group("port")
                    results.append({"ip": ip, "port": port})

    for r in results:
        ecjrpc = ExecutionClientJsonRPC(r["ip"], r["port"], timeout=60)
        node_info = ecjrpc.admin_node_info()
        enodes.append(node_info["enode"])
    for r in results:
        ecjrpc = ExecutionClientJsonRPC(r["ip"], r["port"], timeout=60)
        node_info = ecjrpc.admin_node_info()
        curr_node_enode = node_info["enode"]
        for e in enodes:
            if e != curr_node_enode:
                ecjrpc.admin_add_peer(e)
                time.sleep(1)
                print(f"adding peer {e} to {curr_node_enode}")
