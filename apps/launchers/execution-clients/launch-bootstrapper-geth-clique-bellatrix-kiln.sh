#!/bin/bash

# this file is run in the geth docker via docker-compose entrypoint. 

# args are: <data_dir> <generated_genesis.json> <network_id> <http_port> <http_apis> <ws_port> <ws_apis>

env_vars=( "EXECUTION_DATA_DIR", "EXECUTION_GENESIS", "NETWORK_ID", "EXECUTION_P2P_PORT", "EXECUTION_HTTP_PORT", "EXECUTION_WS_PORT", "HTTP_APIS", "WS_APIS", "IP_ADDR", "NETRESTRICT_RANGE", "TTD")

for var in "${env_vars[@]}" ; do
    if [[ -z "$var" ]]; then
        echo "$var not set"
        exit 1
    fi
done

echo "testnet-password" > /data/geth-account-passwords.txt

while [ ! -f "/data/execution-clients-ready" ]; do
    sleep 1
    echo "Waiting on exeuction genesis"
done

echo "Initing the genesis"
geth init \
    --datadir "$EXECUTION_DATA_DIR" \
    "$EXECUTION_GENESIS"

echo "Starting geth"

python3 /source/apps/store_geth_enr.py --geth-ipc "$EXECUTION_DATA_DIR/geth.ipc" --enode-file "$EXECUTION_DATA_DIR/enodes.txt" & 

geth \
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
  --unlock "0x51Dd070D1f6f8dB48CA5b0E47D7e899aea6b1AF5" --password /data/geth-account-passwords.txt --mine \
  --allow-insecure-unlock \
  --rpc.allow-unprotected-txs \
  --override.terminaltotaldifficulty="$TERMINALTOTALDIFFICULTY" \
  --vmodule=rpc=5 

