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
  --networkid="$NETWORK_ID" \
  --http --http.api "$HTTP_APIS" \
  --http.port "$HTTP_PORT" \
  --http.addr 0.0.0.0 \
  --http.corsdomain "*" \
  --ws --ws.api "$WS_APIS" \
  --ws.port="$WS_PORT" \
  --ws.addr 0.0.0.0 \
  --netrestrict "10.0.20.0/24" \
  --keystore '/source/apps/data/geth-keystores/' \
  --unlock "0x51Dd070D1f6f8dB48CA5b0E47D7e899aea6b1AF5" --password /data/geth-account-passwords.txt --mine \
  --allow-insecure-unlock \
  --rpc.allow-unprotected-txs \
  --vmodule=rpc=5 
