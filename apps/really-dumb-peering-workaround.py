from modules.GethIPCUtils import GethIPC
import time
import re


if __name__ == "__main__":
    with open("/source/docker-compose.yaml", "r") as f:
        data = f.read()

    enodes = []
    geth_data_dir_regex = r"EXECUTION_DATA_DIR=(?P<dir>[a-zA-z0-9\/\-]+)"
    results = re.findall(geth_data_dir_regex, data)
    for r in results:
        geth_ipc = r + "/geth.ipc"
        g = GethIPC(geth_ipc)
        enodes.append(g.get_enode())

    for r in results:
        for e in enodes:
            geth_ipc = r + "/geth.ipc"
            g = GethIPC(geth_ipc)
            if e != g.get_enode():
                print(f"adding peer {e} to {g.get_enode()}")
                g.add_peer(e)
                time.sleep(1)
                # geth doesn't appear to like it when we spam.
