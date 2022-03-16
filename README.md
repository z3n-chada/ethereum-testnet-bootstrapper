# ethereum-testnet-bootstrapper
Allows you to easily create and launch custom testnets locally to test various features. You can use dockers provided by client teams or modify and launch your own execution or consensus layer nodes to test and debug.


How to launch:
```
make clean; make build-bootstrapper; make run-bootstrapper config=/source/configs/...
docker-compose up --force-recreate
```
All of the docker images map the current directory to /source/ so if you would like to customize the configs prepend /source to them,
if you are happy running the defaults then just /config/{path to the config} will suffice. 
## Configurations
All networks are run based on a configuration. This configuration specifies execution and consensus clients, all of the flags that need to be used, and all of the genesis information. When you launch with docker-compose up, a bootstrapper reads the config (the one supplied with run-bootstrapper) and populates the testnet directories and creates the genesis files. This way you don't need to worry about rebuilding if you lauch the same docker-compose file twice. The main portions of the configuration are as follows:
1. files
    - You shouldn't need to edit this, this just sets where files are written so the launching scripts can read them.
2. config-params
    - This is all of the genesis information, an example is given below.
```
config-params:

  deposit-contract-address: "0x8c594691c0e592ffa21f153a16ae41db5befcaaa"
  deposit-chain-id: 0x01000666
  deposit-network-id: 0x01000666

  # used for configuring geth genesis. placed in /data/eth1-genesis.json
  execution-layer:
    seconds-per-eth1-block: 14
    genesis-delay: 0
    genesis-config:
      chainId: 0x01000666
      homesteadBlock: 0
      eip150Block: 0
      eip155Block: 0
      eip158Block: 0
      byzantiumBlock: 0
      constantinopleBlock: 0
      petersburgBlock: 0
      istanbulBlock: 0
      berlinBlock: 0
      londonBlock: 0
      mergeForkBlock: 44
      terminalTotalDifficulty: 90
    clique:
      enabled: True
      signer: "51Dd070D1f6f8dB48CA5b0E47D7e899aea6b1AF5"
      epoch: 3000
    terminal-block-hash: "0x0000000000000000000000000000000000000000000000000000000000000000"
    terminal-block-hash-activation-epoch: 18446744073709551615
  # used for generating the consensus config placed in /data/eth2-config.yaml
  consensus-layer:
    genesis-delay: 224 #lets the clients get to eth1-follow-distance
    preset-base: 'minimal'
    min-genesis-active-validator-count: 18 # custom preseeded into genesis state.

    forks:
      genesis-fork-version: 0x01000666
      genesis-fork-name: "phase0"
      end-fork-name: "bellatrix"

      phase0-fork-version: 0x01000666
      phase0-fork-epoch: 0 # genesis

      altair-fork-version: 0x02000666
      altair-fork-epoch: 2 # slot 48

      bellatrix-fork-version: 0x03000666
      bellatrix-fork-epoch: 4 # slot 96

      sharding-fork-version: 0x04000666
      sharding-fork-epoch: 18446744073709551615
```
3. accounts
    - holds all of the ethereum account information such as the premines, mnemonics and passwords for key files.

4. consensus bootnode
    - which bootnode to use for consensus clients (only implemented one currently)

5. consensus configs
    - holds information for running a consensus client. Clients inherit from these base configurations.
    - if you are using local execution clients you must specify the execution-config as well.
```
consensus-configs:
  base-consensus-client:
    num-nodes: 1            # number of nodes for every client that inherits this config
    num-validators: 6       # number of validators for every client that inherits this config
    # start ports increment each time we have a node.
    start-consensus-p2p-port: 4000    # start port used for discovery
    start-beacon-api-port: 5000   # start port used for the beacon rest API
    start-beacon-rpc-port: 5500
    start-validator-rpc-port: 6500
    start-beacon-metric-port: 8000 # start port used for beacon node metrics.
    start-validator-metric-port: 9000 # start port used for validator client metrics.
    # entrypoints placed here are used by the consensus clients
    local-execution-client: true
    execution-config: "base-geth-execution-client"
    execution-launcher: "/source/apps/launchers/execution-clients/launch-geth-clique.sh"

    http-web3-ip-addr: "127.0.0.1"
    ws-web3-ip-addr: "127.0.0.1"
```
6. execution-configs
    - configs for the execution clients to inherit from.
```
execution-configs:
  base-geth-execution-client:
    client: "geth"
    network-id: 0x01000666
    chain-id: 0x01000666
    http-apis: "admin,net,eth,web3,personal,engine"
    ws-apis: "admin,net,eth,web3,personal,engine"
    execution-http-port: 8645
    execution-ws-port: 8646
    execution-p2p-port: 666
    geth-genesis: "/data/geth-genesis.json"
    terminalTotalDifficulty: 90
```
7. consensus clients
    - which consensus clients to use, and any extra 
## Stress Testing Roadmap
- Network partitions
- Fuzzer generic-modules
- Better metrics

## Trophies
The issues listed here are not neccesarily related to security bugs, they could be edge case scenarios that clients haven't covered. 

- Prysm
    - (non-security) invalid config file parsing for PRESET\_BASE field.
    - (non-security, non-spec) handeling 0 hash for eth1 root hash.
    - (non-security) handle genesis from non-phase0 genesis beaconstates.
- eth2-testnet-genesis
    - (non-security) fix altair beaconstate genesis

# Overview
Dockers contain the cl and the el clients with which they can become nodes on the network. The bootstrapper (ethereum-testnet-bootstrapper) reads the configuration for the testnet and populates all of the required directories.  


