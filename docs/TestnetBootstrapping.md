# Bootstrapping Process
This doc has some notes on the general outline of how we bootstrap a testnet 
given a config file. The config files we use contain all the relevant 
information needed to get all consensus client and execution client pairs up 
and working together.

The general process is broken up into a few main steps. These steps assume that
you have already built all the docker images that we will be using. Each of 
these steps make use of the ``ethereum-testnet-bootstrapper`` docker image. 

To build them simply run: ``make build-dockers``

When using the ethereum-testnet-bootstrapper the configs are stored locally
in the container. Therefore if you make any change to a config file you must
update the bootstrapper first. This can be done via:``make build-bootstrapper``

See the docker section for more information.
## Init
The init phase of bootstrapping is first. This step simply processes the 
etb-config file (/configs) and creates all directories and files that can
be created statically. Files that depend on timestamps for example do not get
created in this step. The init phase will populate the local testnet dir with
all the directories needed for each individual client, populating enr files 
for the consensus boot node, and creating a docker-compose.yaml file to bring
up all the clients and bootstrap the testnet.

To init a testnet simply run: ``make init-testnet config=``

**NOTE: Any changes you make to a config file are not updated until you rebuild the bootstrapper**

The following shows what a local_testnet directory structure looks like after
the init process.

```
...(local project files)...

data/
├── etb-config.yaml
└── local_testnet/
    ├── execution-bootstrapper/
    │   └── jwt-secret-0-0
    ├── lighthouse-geth/
    │   ├── jwt-secret-0
    │   └── node_0/
    │       └── geth/
    ├── lodestar-geth/
    │   ├── jwt-secret-0
    │   └── node_0/
    │       └── geth/
    ├── nimbus-geth/
    │   ├── jwt-secret-0
    │   └── node_0/
    │       └── geth/
    ├── prysm-geth/
    │   ├── jwt-secret-0
    │   └── node_0/
    │       └── geth/
    └── teku-geth/
        ├── jwt-secret-0
        └── node_0/
            └── geth/

```
You are now ready to run a docker testnet locally.
## Bootstrapping/Running
The last phase is bootstrapping. This phase happens when you are ready to run
the testnet. 
## Testnet Directory Structure
When we create a testnet to launch with docker instances we give all the clients a shared directory they can use. This
is the testnet dir.
## Execution Bootstrapping
## Consensus Bootstrapping
# Dockers