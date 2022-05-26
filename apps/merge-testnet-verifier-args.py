"""
    Given an etb-config file create the entrypoint for a merge-testnet-verifier
    container to monitor the clients.
"""

import argparse

from modules.ETBConfig import ETBConfig


def generate_mtv_entrypoint(args):
    """ """
    # we need the ttd for the args
    etb_config = ETBConfig(args.config)
    ttd = etb_config.get("terminal-total-difficulty")
    args = [f"-ttd {ttd}"]
    for name, cc in etb_config.get("all-execution-clients").items():
        for node in range(cc.get("num-nodes")):
            client = cc.get("client")
            ip = cc.get("ip-addr", node)
            port = cc.get("execution-http-port")
            args.append(f"-client {client},http://{ip}:{port}")

    for name, cc in etb_config.get("consensus-clients").items():
        for node in range(cc.get("num-nodes")):
            client = cc.get("client-name")
            print(client)
            ip = cc.get("ip-addr", node)
            port = cc.get("beacon-api-port")
            args.append(f"-client {client},http://{ip}:{port}")
        # do EL first
        # do CLs next.
    return args


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        dest="config",
        required=True,
        help="path to config file to consume for experiment",
    )

    parser.add_argument(
        "--binary",
        dest="binary",
        required=False,
        default=None,
        help="binary to launch, assumes entrypoint in docker is already set.",
    )

    args = parser.parse_args()
    mtv_args = generate_mtv_entrypoint(args)
    print(" ".join(mtv_args))
