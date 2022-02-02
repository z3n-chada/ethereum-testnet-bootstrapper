#!/bin/bash

# this file is run in the geth docker via docker-compose entrypoint. 

# args are: <data_dir> <generated_genesis.json> <network_id> <http_port> <http_apis> <ws_port> <ws_apis>

GETH_DATA_DIR=$1
GENESIS_CONFIG=$2
NETWORK_ID=$3
HTTP_PORT=$4
HTTP_APIS=$5
WS_PORT=$6
WS_APIS=$7

echo "testnet-password" > /data/geth-account-passwords.txt

while [ ! -f "/data/execution-clients-ready" ]; do
    sleep 1
    echo "Waiting on exeuction genesis"
done

echo "Initing the genesis"
geth init \
    --datadir "$GETH_DATA_DIR" \
    "$GENESIS_CONFIG"

echo "Starting geth"
geth \
  --datadir="$GETH_DATA_DIR" \
  --networkid="$NETWORK_ID" --catalyst \
  --http --http.api "$HTTP_APIS" \
  --http.port "$HTTP_PORT" \
  --http.addr 0.0.0.0 \
  --http.corsdomain "*" \
  --ws --ws.api "$WS_APIS" \
  --ws.port="$WS_PORT" \
  --ws.addr 0.0.0.0 \
  --allow-insecure-unlock \
  --netrestrict "10.0.20.0/24" \
  --vmodule=rpc=5 
