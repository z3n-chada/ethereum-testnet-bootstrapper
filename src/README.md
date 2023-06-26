# Default Apps included in ethereum-testnet-bootstrapper

## bootstrap-testnet
Provides a simple app to create testnets. This is what is used in the init-testnet and make clean steps. For more 
information see [Testnet Lifecycle](../docs/TestnetLifecycle.md)

## node-watch
Runs in the background and pings all the clients to deteremine if there are any forks and when the last justified
and finalized checkpoints were. This is useful for monitoring the testnet and determining if there are any issues. 
Example output:
```
INFO:testnet-monitor:Number of forks: 0
CurrentHead: (slot: 560, root: 8d657a, graffiti: teku-besu-0), Checkpoints: (justified: (69, de5543) : finalized: (68, f0d1a5)): [lighthouse-besu-0, lighthouse-geth-0, lighthouse-nethermind-0, lodestar-besu-0, lodestar-geth-0, lodestar-nethermind-0, nimbus-besu-0, nimbus-geth-0, nimbus-nethermind-0, prysm-besu-0, prysm-geth-0, prysm-nethermind-0, teku-besu-0, teku-geth-0, teku-nethermind-0, teku-whale-0]
```
This shows us that the current head in all client (since there are zero forks) is slot 560 with root 8d657a and it was 
proposed by teku-besu-0 (by default graffiti is the client-instance name). Additionally, the last justified checkpoint
is epoch 69 with root de5543 and the last finalized checkpoint is epoch 68 with root f0d1a5. Note roots are the last 6 
digits of the root to make it easier to read.

The client instances in the brackets shows which clients have this view. If there was a fork you'd have multiple 
CurrentHead lines with the different nodes with this view listed in the brackets.

## tx-spammer
This app is used to spam the network with transactions. It will send transactions using 
[tx-fuzz](https://github.com/MariusVanDerWijden/tx-fuzz)

The tx-spammer allows to specify when to start spamming the network, but by default it uses the beginning of the second
CL epoch.

## validator-operation-spammer
This app is used to spam the network with validator operations. It will send validator operations using ethdo. If there
are validators that have keys that weren't deployed in genesis it will use these keys for deposits. You can also specify 
to use non-valid keys (keys that aren't accounted for with validators) this will lead to an inactivity leak.

## beacon-metric-gazer
This app is used to collect metrics from the beacon chain on an epoch basis. It uses 
[beacon-metric-gazer](https://github.com/dapplion/beacon-metrics-gazer) to collect the metrics.