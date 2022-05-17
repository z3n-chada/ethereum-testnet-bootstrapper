# ethereum-testnet-bootstrapper
Allows you to easily create and launch custom testnets locally to test various features. You can use dockers provided by client teams or modify and launch your own execution or consensus layer nodes to test and debug.


How to launch:
```
make clean; make build-bootstrapper; make init-bootstrapper config=configs/...
docker-compose up --force-recreate --remove-orphans
```
All of the docker images map the current directory to /source/ so if you would like to customize the configs prepend /source to them,
if you are happy running the defaults then just /config/{path to the config} will suffice. 

## Trophies
The issues listed here are not neccesarily related to security bugs, they could be edge case scenarios that clients haven't covered. Bugs listed here are from local tests and using the Antithesis testing platform.

- prysm
    - (non-security) invalid config file parsing for PRESET\_BASE field.
    - (non-security, non-spec) handeling 0 hash for eth1 root hash.
    - (non-security) handle genesis from non-phase0 genesis beaconstates.
    - (non-security) api /eth/vX/beacon/headers/X uses the incorrect htr (SignedBeaconBlockHeader instead of BeaconBlockHeader)
    - (race condition) [race condition for eth1data](https://github.com/prysmaticlabs/prysm/issues/10531)
    - (race condition) [race condition for reValidatePeer](https://github.com/prysmaticlabs/prysm/issues/10530)
- nimbus
    - several nil dereferences on Eth1Monitor
    - (networking) undisclosed
    - undisclosed
- lighthouse
    - (logic) [attestation for future blocks](https://github.com/sigp/lighthouse/pull/3183)
- nethermind
    - (non-security) [cascading errors duu to bad CLI args](https://github.com/NethermindEth/nethermind/issues/3942)
    - undisclosed
- geth
    - undisclosed
- eth2-testnet-genesis
    - (non-security) fix altair beaconstate genesis

# Overview
Dockers contain the cl and the el clients with which they can become nodes on the network. The bootstrapper (ethereum-testnet-bootstrapper) reads the configuration for the testnet and populates all of the required directories.  


