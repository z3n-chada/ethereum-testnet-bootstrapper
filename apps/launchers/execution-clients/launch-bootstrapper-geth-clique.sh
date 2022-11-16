#!/bin/bash

# this file is run in the geth docker via docker-compose entrypoint. 

# args are: <data_dir> <generated_genesis.json> <network_id> <http_port> <http_apis> <ws_port> <ws_apis>

#CHAIN_ID: 16778854,
#END_FORK_NAME: bellatrix,
#EXECUTION_DATA_DIR: /data/local_testnet/execution-bootstrapper,
#EXECUTION_ENGINE_PORT: 8647, 
#EXECUTION_HTTP_PORT: 8645, 
#EXECUTION_P2P_PORT: 666,
#EXECUTION_WS_PORT: 8646, 
#GETH_GENESIS_FILE: /data/geth-genesis.json, 
#HTTP_APIS: 'admin,net,eth,web3,personal,engine',
#IP_ADDR: 10.0.20.2
#NETRESTRICT_RANGE: 10.0.20.0/24
#NETWORK_ID: 16778854,
#TERMINAL_TOTAL_DIFFICULTY: 256,
#WS_APIS: 'admin,net,eth,web3,personal,engine'

env_vars=( "EXECUTION_DATA_DIR" "GETH_GENESIS_FILE" "NETWORK_ID" "EXECUTION_P2P_PORT" "EXECUTION_HTTP_PORT" "EXECUTION_WS_PORT" "HTTP_APIS" "WS_APIS" "IP_ADDR" "NETRESTRICT_RANGE" "END_FORK_NAME" "EXECUTION_LOG_LEVEL")

for var in "${env_vars[@]}" ; do
    if [[ -z "${!var}" ]]; then
        echo "$var not set"
        exit 1
    fi
done

while [ ! -f "$EXECUTION_CHECKPOINT_FILE" ]; do
    sleep 1
    echo "Waiting on exeuction genesis"
done

echo "geth got a valid env-var set"

ADDITIONAL_ARGS="--verbosity=$EXECUTION_LOG_LEVEL"

if [[ "$END_FORK_NAME" = "bellatrix" ]]; then
    # since we are doing the merge in the consensus
    # we need to add the terminal total difficutly override
    echo "Geth client is taking part in a merge testnet, overriding the TTD"
    if [[ -z "$TERMINAL_TOTAL_DIFFICULTY" ]]; then
        echo "We are doing a merge consensus test but no terminal total difficulty was applied"
        exit 1
    fi
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --override.terminaltotaldifficulty=$TERMINAL_TOTAL_DIFFICULTY"
else
    echo "Geth not overriding terminal total difficulty. Got an END_FORK:$END_FORK_NAME"
    echo "if you are trying to test a merge configuration check that the config file is sane"
fi 

echo "testnet-password" > /data/geth-account-passwords.txt


echo "Initing the genesis"
geth init \
    --datadir "$EXECUTION_DATA_DIR" \
    "$GETH_GENESIS_FILE"

#while [ ! -f "$EXECUTION_BOOTNODE_ENODE_FILE" ]; 
#do sleep 1
#    echo "waiting for the execution bootnode to come up."
#done

if [ -n "$JWT_SECRET_FILE" ]; then
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --authrpc.port=$EXECUTION_ENGINE_AUTH_PORT --authrpc.addr=0.0.0.0 --authrpc.vhosts=\"*\" --authrpc.jwtsecret=$JWT_SECRET_FILE"
    echo "Geth is using JWT"
fi
#--nodekeyhex="522d5e0fd25b33b2d9a28c0376013c3704aa79c1dc5424d107531f22d54f9d58" \
echo "Starting geth"
geth \
  --datadir="$EXECUTION_DATA_DIR" \
  --networkid="$NETWORK_ID" \
  --port="$EXECUTION_P2P_PORT" \
  --nat="extip:$IP_ADDR" \
  --http --http.api "$HTTP_APIS" \
  --http.port="$EXECUTION_HTTP_PORT" \
  --http.addr=0.0.0.0 \
  --http.corsdomain="*" \
  --ws --ws.api="$WS_APIS" \
  --ws.port="$EXECUTION_WS_PORT" \
  --ws.addr=0.0.0.0 \
  --netrestrict="$NETRESTRICT_RANGE" \
  --keystore="/source/apps/data/geth-keystores/" \
  --unlock="0x51Dd070D1f6f8dB48CA5b0E47D7e899aea6b1AF5" --password=/data/geth-account-passwords.txt --mine \
  --allow-insecure-unlock \
  --rpc.allow-unprotected-txs \
  --maxpeers=200 $ADDITIONAL_ARGS \
  --vmodule=rpc=5 

#--v5disc \
