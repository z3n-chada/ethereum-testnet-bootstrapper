from modules.TestnetMonitor import TestnetMonitor, CurrentHeads, EverySlotInterval
from modules.ETBConfig import ETBConfig

if __name__ == "__main__":
    etb_config = ETBConfig("configs/minimal/geth-capella.yaml")
    tm = TestnetMonitor(etb_config)
    tm.init()
    # print(tm.get_slot())
    # tm.wait_for_slot(10)
    # print(tm.get_slot())
    # tm.wait_for_slot(65)
    # print(tm.get_epoch())

    cl_clients = etb_config.get_consensus_clients()
    interval = EverySlotInterval()  # do it every slot
    get_heads_handler = CurrentHeads(interval, clients=cl_clients)
    results = dict(get_heads_handler.perform_actions())
    for client in results:
        print(f"{client}: {results[client]}")
