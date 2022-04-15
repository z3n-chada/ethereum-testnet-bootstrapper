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
The issues listed here are not neccesarily related to security bugs, they could be edge case scenarios that clients haven't covered. 

- Prysm
    - (non-security) invalid config file parsing for PRESET\_BASE field.
    - (non-security, non-spec) handeling 0 hash for eth1 root hash.
    - (non-security) handle genesis from non-phase0 genesis beaconstates.
    - (non-security) api /eth/vX/beacon/headers/X uses the incorrect htr (SignedBeaconBlockHeader instead of BeaconBlockHeader)
- eth2-testnet-genesis
    - (non-security) fix altair beaconstate genesis
- nimbus
    - several nil dereferences on Eth1Monitor
    - undisclosed
- geth
    - undisclosed

# Overview
Dockers contain the cl and the el clients with which they can become nodes on the network. The bootstrapper (ethereum-testnet-bootstrapper) reads the configuration for the testnet and populates all of the required directories.  


