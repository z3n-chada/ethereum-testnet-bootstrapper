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
├── docker-compose.yaml
├── data/
│   ├── etb-config.yaml
│   └── local_testnet/
│       ├── execution-bootstrapper/
│       │   └── jwt-secret-0
│       ├── lighthouse-geth/
│       │   ├── jwt-secret-0
│       │   └── node_0/
│       │       └── geth/
│       ├── lodestar-geth/
│       │   ├── jwt-secret-0
│       │   └── node_0/
│       │       └── geth/
│       ├── nimbus-geth/
│       │   ├── jwt-secret-0
│       │   └── node_0/
│       │       └── geth/
│       ├── prysm-geth/
│       │   ├── jwt-secret-0
│       │   └── node_0
│       │       └── geth/
│       └── teku-geth/
│           ├── jwt-secret-0
│           └── node_0/
│               └── geth/

```
You are now ready to run a docker testnet locally.
## Bootstrapping/Running
The last phase is bootstrapping. This phase happens when you are ready to run
the testnet. This phase makes extensive use of checkpoint files. The reason for
this is that we bring up every single docker container including the 
bootstrapper. Checkpoint files exist to allow all of the containers to know 
when their relevant data is ready for use and their dependent docker images are
running and ready to accept connections. The following sections are ordered in 
terms of their checkpoint files.
### etb-config-checkpoint
1. ``[ethereum-testnet-bootstrpper]``: open the etb-config-file and set the current time
write the file. 
2. ``[ethereum-testnet-bootstrapper]``: write the checkpoint file ``etb-config-checkpoint``
to signal to the docker images that the etb-config file is ready to be opened.
### consensus-bootnode-checkpoint
There are no dependencies. 
1. ``[ethereum-testnet-bootstrapper]``: write the checkpoint file ``consensus-bootnode-checkpoint``
to signal the CL bootnode to come online.
### execution-checkpoint-file
1. ``[ethereum-testnet-bootstrapper]``: create the genesis json for all the EL clients.
2. ``[ethereum-testnet-bootstrapper]``: write the checkpoint file ``execution-checkpoint``
to signal all the EL clients to come online.
3. ``[ethereum-testnet-boostrapper]``: after some time we also link together all the EL clients via ``admin_addPeer()`` calls.
   4.   it was previously possible to run erigon, but as they don't implement this API interface we have dropped support to speed up development :(
   5. support may later be added, you can see how it was previously done before the post-merge-genesis-rework branch was merged in.
### consensus-checkpoint-file
1. ``[ethereum-testnet-bootstrapper]``: once execution has kicked off we build the config.yaml and genesis.ssz file and then populate all of the cl client dirs with the neccessary files. (genesis.ssz, config.yaml, validator-key dirs, etc..)
2. ``[ethereum-testnet-bootstrapper]``: write the checkpoint file ``consensus-checkpoint`` to signal all the CL clients to come up.

TODO: finish this doc.