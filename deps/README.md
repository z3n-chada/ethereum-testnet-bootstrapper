# Client Dependencies Overview
The following ``/deps/`` folder contains all the files you need to modify in order to change which builds of clients and 
what arguments they use at run time. The dockerfiles and launchers are found in their respective folders. New features 
or configs can be added via a PR or an issue on this repo. 

## Docker Dependencies
Updates to builds are done here. If client teams wish to modify the branch/build steps for a client they can do so here.

### Base Images (/deps/dockers/base-images/)
1. ``etb-client-builder`` -> all client builders inherit from this image.
2. ``etb-client-runner`` -> once built all clients binaries are copied into this image. (becomes ``etb-all-clients``)

### Consensus Layer Clients (/deps/dockers/cl/)
The following are the default dockers built here. They are build with a bash script, so building multiple versions of
images is possible. The dockers are named via ``LHS:RHS`` from ``LHS_RHS.dockerfile`` Modify the ``etb-client-runner`` to
pull from the new image you define. 
1. ``prysm_develop`` -> instrumented prysm built from the latest develop branch.
2. ``lighthouse_stable`` -> instrumented lighthouse client built from the latest stable branch.
3. ``lodestar_master`` -> lodestar built from master. (instrumentation for typescript unavailable)
4. ``teku_master`` -> teku built from master. (java is automatically instrumented)
5. ``nimbus_stable`` -> instrumented nimbus built from the latest stable branch.

### Execution Layer Clients (/deps/dockers/el)
1. ``geth_master`` -> instrumented geth client built from latest master branch.
2. ``besu_develop`` -> besu client built from the latest develop branch. (java auto instrumented)
3. ``nethermind_master`` -> nethermind client built from the latest client (no instrumentation)

### Fuzzers (/deps/dockers/fuzzers)
TODO: finish writing this part. 

## Launcher Dependencies
When a testnet is bootstrapped and run we reference the ``/deps/launchers`` directory for the entrypoint of their dockers.
By default, the ``/apps/modules/DockerCompose.py`` and ``/apps/modules/ETBConfig.py`` together dictate what env vars the
launchers will have access to at runtime. There is also a spot in the ``etb-config`` file to put static env-vars. This is
done via an ``additional-env-vars:`` entry. For example:
```yaml
  prysm-geth:
    client-name: 'prysm'
    # docker-compose
    image: "etb-all-clients"
    tag: "latest"
    container-name: "prysm-client-geth"
    entrypoint: "/source/deps/launchers/cl/launch-prysm.sh"
    start-ip-addr: "10.0.20.10"
    depends: "ethereum-testnet-bootstrapper"
    # beacon/validator flags
    num-nodes: 1 # how many beacon nodes
    consensus-config: "base-consensus-client"

    consensus-bootnode-config: "eth2-bootnode-config"

    local-execution-client: true
    execution-config: "geth-execution-config"
    execution-launcher: "/source/deps/launchers/el/launch-geth.sh"

    testnet-dir: '/data/local_testnet/prysm-geth'
    jwt-secret-file: "/data/local_testnet/prysm-geth/jwt-secret"

    validator-offset-start: 0 # so validators of different clients don't overlap
    # args specific to prysm nodes, these are loaded into the dockers env at runtime.
    additional-env:
      prysm-debug-level: "debug"
      wallet-path: '/data/local_testnet/prysm-geth/wallet-password.txt'
      validator-password: "testnet-password"
```
Here every ``prysm-geth`` client will have an additional env set:
```bash
PRYSM_DEBUG_LEVEL="debug"
WALLET_PATH='/data/local_testnet/prysm-geth/wallet-password.txt'
VALIDATOR_PASSWORD="testnet-password"
```

By default every consensus-layer client comes with the following env-vars. 
```python
# defined and calculated in /apps/modules/DockerCompose.py based on the supplied config file.
base_consensus_env_vars = [
    "preset-base",
    "testnet-dir",
    "node-dir",
    "ip-addr",
    "consensus-p2p-port",
    "beacon-api-port",
    "graffiti",
    "netrestrict-range",
    "beacon-metric-port",
    "beacon-rpc-port",
    "validator-rpc-port",
    "validator-metric-port",
    "execution-launcher",
    "local-execution-client",
    "consensus-target-peers",
    "consensus-bootnode-enr-file",
    "consensus-checkpoint-file",
    "ws-web3-ip-addr",
    "http-web3-ip-addr",
    "execution-bootnode",
]

base_execution_env_vars = [
    "ip-addr",
    "execution-data-dir",
    "execution-p2p-port",
    "execution-http-port",
    "execution-ws-port",
    "http-apis",
    "ws-apis",
    "terminal-total-difficulty",
    "chain-id",
    "network-id",
    "netrestrict-range",
    "geth-genesis-file",
    "besu-genesis-file",
    "nether-mind-genesis-file",
    "execution-checkpoint-file",
    "execution-log-level",
]
```
If more are needed you can submit a PR. 

### Execution Launchers
TODO: finish this
### Consensus Launchers
TODO: finish this