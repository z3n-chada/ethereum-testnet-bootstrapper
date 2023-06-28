![etb-all-clients](https://github.com/antithesishq/ethereum-testnet-bootstrapper/actions/workflows/etb-all-clients.yml/badge.svg)

# ethereum-testnet-bootstrapper

## Quick Start
If starting from a fresh clone you must build the bootstrapper (bootstrapper.Dockerfile) as well as the client images the configs
depend on. (deps/dockers/build_dockers.sh)

You can build both of these via:
```bash
make build-all-images
```
or seperately via:
```bash
make build-bootstrapper
make build-client-images
```

All images can be build without the cache via:
```bash
make rebuild-all-images
# or individually
make rebuild-bootstrapper
make rebuild-client-images
```

Once the images are built you can launch a testnet.
```bash
# clean the last experiment if any
make clean 

# initialize the testnet
make init-testnet config=configs/EXPERIMENT_CONFIG
# for example run a minimal testnet with all client pairs:
make init-testnet config=configs/minimal-testnet.yaml
 
# bootstrap and run the testnet
docker-compose up --force-recreate --remove-orphans
```

The testnet commands can also be run with various logging levels:

debug v.s. info
```
make init-testnet config=configs/minimal-testnet.yaml log_level=info

docker run -it -v /0xtylerholmes/git/ethereum-testnet-bootstrapper/:/source/ -v /0xtylerholmes/git/ethereum-testnet-bootstrapper/data/:/data ethereum-testnet-bootstrapper --config configs/minimal-testnet.yaml --init-testnet --log-level info
2023-06-28 17:56:09,645 [INFO] testnet_bootstrapper has started.
2023-06-28 17:56:09,697 [INFO] populating client directories and jwt-secret files
2023-06-28 17:56:09,698 [INFO] populating validator keystores
2023-06-28 17:56:11,775 [INFO] writing etb-config file..
2023-06-28 17:56:11,807 [INFO] writing docker-compose file..

```

```
make init-testnet config=configs/minimal-testnet.yaml log_level=debug
docker run -it -v /0xtylerholmes/git/ethereum-testnet-bootstrapper/:/source/ -v /0xtylerholmes/git/ethereum-testnet-bootstrapper/data/:/data ethereum-testnet-bootstrapper --config configs/minimal-testnet.yaml --init-testnet --log-level debug

...
2023-06-28 17:57:53,922 [DEBUG] populating keystores for client: lighthouse-nethermind-0
2023-06-28 17:57:53,922 [DEBUG] min_ndx: 48, max_ndx: 52
2023-06-28 17:57:53,923 [DEBUG] Generating keystores for validators 48 to 52.
2023-06-28 17:57:53,923 [DEBUG] Running command: ['eth2-val-tools', 'keystores', '--source-min', '48', '--source-max', '52', '--source-mnemonic', 'ocean style run case glory clip into nature guess jacket document firm fiscal hello kite disagree symptom tide net coral envelope wink render festival', '--out-loc', '/data/local-testnet/lighthouse-nethermind/node_0/keystores']
2023-06-28 17:57:54,059 [DEBUG] populating keystores for client: lodestar-nethermind-0
2023-06-28 17:57:54,059 [DEBUG] min_ndx: 52, max_ndx: 56
2023-06-28 17:57:54,059 [DEBUG] Generating keystores for validators 52 to 56.
2023-06-28 17:57:54,059 [DEBUG] Running command: ['eth2-val-tools', 'keystores', '--source-min', '52', '--source-max', '56', '--source-mnemonic', 'ocean style run case glory clip into nature guess jacket document firm fiscal hello kite disagree symptom tide net coral envelope wink render festival', '--out-loc', '/data/local-testnet/lodestar-nethermind/node_0/keystores']
2023-06-28 17:57:54,193 [DEBUG] populating keystores for client: nimbus-nethermind-0
2023-06-28 17:57:54,193 [DEBUG] min_ndx: 56, max_ndx: 60
2023-06-28 17:57:54,193 [DEBUG] Generating keystores for validators 56 to 60.
2023-06-28 17:57:54,193 [DEBUG] Running command: ['eth2-val-tools', 'keystores', '--source-min', '56', '--source-max', '60', '--source-mnemonic', 'ocean style run case glory clip into nature guess jacket document firm fiscal hello kite disagree symptom tide net coral envelope wink render festival', '--out-loc', '/data/local-testnet/nimbus-nethermind/node_0/keystores']
2023-06-28 17:57:54,351 [INFO] writing etb-config file..
2023-06-28 17:57:54,381 [INFO] writing docker-compose file..
2023-06-28 17:57:54,473 [DEBUG] testnet_bootstrapper has finished init-ing the testnet.

```

You can check the status of an experiment by attaching to the node-watch container.
```bash
docker attach node-watch-0
```

The output of which will look something like this:
```
2023-06-28 17:45:15,510 [INFO] Expected slot: 37
2023-06-28 17:45:15,615 [INFO] no forks detected.
2023-06-28 17:45:15,615 [INFO] heads:
2023-06-28 17:45:15,615 [INFO] ('37', '8deee20a', 'prysm-nethermind-0'): ['lighthouse-besu-0', 'lighthouse-geth-0', 'lighthouse-nethermind-0', 'lodestar-besu-0', 'lodestar-geth-0', 'lodestar-nethermind-0', 'nimbus-besu-0', 'nimbus-geth-0', 'nimbus-nethermind-0', 'prysm-besu-0', 'prysm-geth-0', 'prysm-nethermind-0', 'teku-besu-0', 'teku-geth-0', 'teku-nethermind-0']

2023-06-28 17:45:15,615 [INFO] checkpoints:
2023-06-28 17:45:15,616 [INFO] finalized: (2, 0x92fd9d9f), current justified: (3, 0x9770ab26), previous justified: (2, 0x92fd9d9f): ['lighthouse-besu-0', 'lighthouse-geth-0', 'lighthouse-nethermind-0', 'lodestar-besu-0', 'lodestar-geth-0', 'lodestar-nethermind-0', 'nimbus-besu-0', 'nimbus-geth-0', 'nimbus-nethermind-0', 'prysm-besu-0', 'prysm-geth-0', 'prysm-nethermind-0', 'teku-besu-0', 'teku-geth-0', 'teku-nethermind-0']

```
Here the heads report shows you a series of head reports:
- `(head_slot, last 4 bytes of state root, proposer) : [clients with this view].`

If there are forks you would see multiple entries.

The checkpoints report shows you the checkpoints in 
- `(epoch, last 8 bytes of root) : [clients with this view]` 


NOTE: it may take several slots for all of the nodes to come up. This is normal and you can ignore all the `ERROR` messages 
until the nodes are up.

If nodes become unresponsive these will be reported via `Unreachable clients`. For example if `prysm-nethermind-0` went offline:
```
2023-06-28 17:50:07,065 [ERROR] Maximum number of retries reached for http://10.0.20.110:5000
2023-06-28 17:50:12,108 [ERROR] Maximum number of retries reached for http://10.0.20.110:5000
2023-06-28 17:50:17,157 [ERROR] Maximum number of retries reached for http://10.0.20.110:5000
2023-06-28 17:50:22,207 [ERROR] Maximum number of retries reached for http://10.0.20.110:5000
2023-06-28 17:50:27,235 [ERROR] Maximum number of retries reached for http://10.0.20.110:5000
2023-06-28 17:50:32,277 [ERROR] Maximum number of retries reached for http://10.0.20.110:5000
2023-06-28 17:50:32,283 [INFO] no forks detected.
2023-06-28 17:50:32,284 [INFO] heads:
2023-06-28 17:50:32,284 [INFO] ('87', 'e20b6df5', 'lighthouse-geth-0'): ['lighthouse-besu-0', 'lighthouse-geth-0', 'lighthouse-nethermind-0', 'lodestar-besu-0', 'lodestar-geth-0', 'lodestar-nethermind-0', 'nimbus-besu-0', 'nimbus-geth-0', 'nimbus-nethermind-0', 'prysm-besu-0', 'prysm-geth-0', 'teku-besu-0', 'teku-geth-0', 'teku-nethermind-0']
Unreachable clients: ['prysm-nethermind-0']

2023-06-28 17:50:32,284 [INFO] checkpoints:
2023-06-28 17:50:32,284 [INFO] finalized: (9, 0x5b6005ad), current justified: (10, 0x8b44c0b0), previous justified: (9, 0x5b6005ad): ['lighthouse-besu-0', 'lighthouse-geth-0', 'lighthouse-nethermind-0', 'lodestar-besu-0', 'lodestar-geth-0', 'lodestar-nethermind-0', 'nimbus-besu-0', 'nimbus-geth-0', 'nimbus-nethermind-0', 'prysm-besu-0', 'prysm-geth-0', 'teku-besu-0', 'teku-geth-0', 'teku-nethermind-0']
Unreachable clients: ['prysm-nethermind-0']
```

Additionally, if a client gets behind it may be reported as a fork (e.g. if `prysm-nethermind-0` came back online but wasn't caught up):
```
2023-06-28 17:52:36,370 [INFO] Expected slot: 111
2023-06-28 17:52:36,461 [INFO] detected 1 forks.
2023-06-28 17:52:36,461 [INFO] heads:
2023-06-28 17:52:36,461 [INFO] ('111', '0d09c363', 'lighthouse-besu-0'): ['lighthouse-besu-0', 'lighthouse-geth-0', 'lighthouse-nethermind-0', 'lodestar-besu-0', 'lodestar-geth-0', 'lodestar-nethermind-0', 'nimbus-besu-0', 'nimbus-geth-0', 'nimbus-nethermind-0', 'prysm-besu-0', 'prysm-geth-0', 'teku-besu-0', 'teku-geth-0', 'teku-nethermind-0']
('110', '177a7045', 'lighthouse-geth-0'): ['prysm-nethermind-0']

2023-06-28 17:52:36,461 [INFO] checkpoints:
2023-06-28 17:52:36,461 [INFO] finalized: (11, 0x97471f72), current justified: (12, 0xffcd9523), previous justified: (11, 0x97471f72): ['lighthouse-besu-0', 'lighthouse-geth-0', 'lighthouse-nethermind-0', 'lodestar-besu-0', 'lodestar-geth-0', 'lodestar-nethermind-0', 'nimbus-besu-0', 'nimbus-geth-0', 'nimbus-nethermind-0', 'prysm-besu-0', 'prysm-geth-0', 'prysm-nethermind-0', 'teku-besu-0', 'teku-geth-0', 'teku-nethermind-0']
```