# ethereum-testnet-bootstrapper
Allows you to easily create and launch custom testnets locally to test various features. You can use dockers provided by client teams or modify and launch your own execution or consensus layer nodes to test and debug.


How to launch:
```
make clean; make build-bootstrapper; make run-bootstrapper config=/configs/...
docker-compose up --force-recreate
```
## Implemented Configurations

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
