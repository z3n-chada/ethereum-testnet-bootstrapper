#!/bin/bash

# this file is run in the geth docker via docker-compose entrypoint. 

# args are: <data_dir> <generated_genesis.json> <network_id> <http_port> <http_apis> <ws_port> <ws_apis>
#GETH_DATA_DIR=$1
#GENESIS_CONFIG=$2
#NETWORK_ID=$3
#HTTP_PORT=$4
#HTTP_APIS=$5
#WS_PORT=$6
#WS_APIS=$7
#IP_ADDR=$8
#NET_RESTRICT=$9
#TTD=${10}
#P2P_PORT=${11}
#BOOTNODE_ENR
env_vars=( "BOOTNODE_ENR", "EXECUTION_DATA_DIR", "EXECUTION_GENESIS", "NETWORK_ID", "EXECUTION_P2P_PORT", "EXECUTION_HTTP_PORT", "EXECUTION_WS_PORT", "HTTP_APIS", "WS_APIS", "IP_ADDR", "NETRESTRICT_RANGE", "TERMINALTOTALDIFFICULTY")

for var in "${env_vars[@]}" ; do
    if [[ -z "$var" ]]; then
        echo "$var not set"
        exit 1
    fi
done

echo "Lauching execution client"

echo "testnet-password" > /data/geth-account-passwords.txt

while [ ! -f "/data/execution-clients-ready" ]; do
    sleep 1
    echo "Waiting on exeuction genesis"
done
echo "Detected execution genesis"

while [ ! -f "/data/local_testnet/execution-bootstrapper/enodes.txt" ]; do
    sleep 1
    echo "Waiting on the enodes /data/local_testnet/execution-bootstrapper/enodes.txt"
done
echo "found enodes"
ENODES=`cat data/local_testnet/execution-bootstrapper/enodes.txt`
echo $ENODES
echo "Initing the genesis"
geth init \
    --datadir "$EXECUTION_DATA_DIR" \
    "$EXECUTION_GENESIS"

echo "Starting geth"

geth \
  --bootnodes="$ENODES" \
  --datadir="$EXECUTION_DATA_DIR" \
  --networkid="$NETWORK_ID" \
  --port "$EXECUTION_P2P_PORT" \
  --nat "extip:$IP_ADDR" \
  --http --http.api "$HTTP_APIS" \
  --http.port "$EXECUTION_HTTP_PORT" \
  --http.addr 0.0.0.0 \
  --http.corsdomain "*" \
  --ws --ws.api "$WS_APIS" \
  --ws.port="$EXECUTION_WS_PORT" \
  --ws.addr 0.0.0.0 \
  --netrestrict "$NETRESTRICT_RANGE" \
  --keystore '/source/apps/data/geth-keystores/' \
  --rpc.allow-unprotected-txs \
  --override.terminaltotaldifficulty="$TERMINALTOTALDIFFICULTY" \
  --vmodule=rpc=5 

