# Overview
All scripts and source are located here. 
1. / the root directory contains python modules for accomplishing various tasks. These can be referenced in config files as entrypoints for various images.
    - For example bootstrap\testnet.py is responsible for creating everything needed to lauch a testnet.
2. launchers/ contain shell scripts that launch various execution and consensus layer nodes.
3. modules/ contain some python modules useful for making "script nodes" which perform desired tasks such as mining, submitting transactions, or bootstrapping custom environments.

## Current generic-modules (scripts that can run as entrypoints in local-testnet):
### Geth-Miner
- geth-start-miner.py
```
usage: start-geth-miner.py [-h] [--delay DELAY] [--num-threads NUM_THREADS] [--geth-ipc GETH_IPC] [--etherbase ETHERBASE] [--status-delay STATUS_DELAY] [--num-blocks NUM_BLOCK] [--log-file LOG_FILE]

options:
  -h, --help            show this help message and exit
  --delay DELAY         time after the ipc file is available to wait before mining.
  --num-threads NUM_THREADS
                        number of mining threads to use
  --geth-ipc GETH_IPC   geth.ipc path to start mining
  --etherbase ETHERBASE
                        default public key to send mining profits too.
  --status-delay STATUS_DELAY
                        how often to show status of the pending block
  --num-blocks NUM_BLOCK
                        number of blocks to mine before exiting
  --log-file LOG_FILE   if specified where to log status of miner
```
Starts a miner on a given geth node and profiles the rate of blocks and difficulty increase. This can be used not only to mine transactions, but to also profile your setup to set good values for mergeForkBlock and TotalTerminalDifficulty in the execution genesis params in the config file you wish to run. 

For example after running and reaching genesis you can check the output from the script: 
```
...
curr_difficulty: 259235, curr_block: 1468, run_time=3789
curr_difficulty: 260371, curr_block: 1478, run_time=3819
curr_difficulty: 261514, curr_block: 1487, run_time=3849
curr_difficulty: 262789, curr_block: 1497, run_time=3879
```
and now set your TTD and mergeForkBlock in the execution parameters such that consensus MERGE\_FORK\_EPOCH -> TTD -> mergeForkBlock
### Deploy-Deposits
- deploy-deposits.py
Deploys a range of deposits so you can add new nodes to the system as time goes on. This is useful to slowly increase the validator count as time goes on.
### Random-Transactions
Given a start time and end time send random transactions to and from specified accounts
