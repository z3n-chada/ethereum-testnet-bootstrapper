#!/bin/bash

# this file is run in the geth docker via docker-compose entrypoint. 

# args are: <data_dir> <generated_genesis.json> <network_id> <http_port> <http_apis> <ws_port> <ws_apis>

env_vars=( "EXECUTION_DATA_DIR" "GETH_EXECUTION_GENESIS" "NETWORK_ID" "EXECUTION_P2P_PORT" "EXECUTION_HTTP_PORT" "EXECUTION_WS_PORT" "HTTP_APIS" "WS_APIS" "IP_ADDR" "NETRESTRICT_RANGE" "END_FORK")

for var in "${env_vars[@]}" ; do
    if [[ -z "$var" ]]; then
        echo "$var not set"
        exit 1
    fi
done

echo "geth got a valid env-var set"

MERGE_ARGS=""

if [[ "$END_FORK" = "bellatrix" ]]; then
    # since we are doing the merge in the consensus
    # we need to add the terminal total difficutly override
    echo "Geth client is taking part in a merge testnet, overriding the TTD"
    if [[ -z "$TERMINALTOTALDIFFICULTY" ]]; then
        echo "We are doing a merge consensus test but no terminal total difficulty was applied"
        exit 1
    fi
    MERGE_ARGS="--override.terminaltotaldifficulty=$TERMINALTOTALDIFFICULTY"
    echo "using $MERGE_ARGS"
else
    echo "Geth not overriding terminal total difficulty. Got an END_FORK:$END_FORK"
    echo "if you are trying to test a merge configuration check that the config file is sane"
fi 

echo "testnet-password" > /data/geth-account-passwords.txt

while [ ! -f "/data/execution-clients-ready" ]; do
    sleep 1
    echo "Waiting on exeuction genesis"
done

echo "Initing the genesis"
geth init \
    --datadir "$EXECUTION_DATA_DIR" \
    "$GETH_EXECUTION_GENESIS"


echo "starting the python script to save the enodes"
#python3 /source/apps/store_geth_enr.py --geth-ipc "$EXECUTION_DATA_DIR/geth.ipc" --enode-file "$EXECUTION_DATA_DIR/enodes.txt" & 
( sleep 5; geth attach $EXECUTION_DATA_DIR/geth.ipc --exec admin.nodeInfo.enr | tr -d "\"" > $EXECUTION_DATA_DIR/enodes.txt ) &
( sleep 30; python3 /source/apps/really-dumb-peering-workaround.py) &


#while [ ! -f "$EXECUTION_BOOTNODE_ENODE_FILE" ]; 
#do sleep 1
#    echo "waiting for the execution bootnode to come up."
#done

ENODE="$EXECUTION_BOOTNODE_ENODE@$EXECUTION_BOOTNODE_START_IP_ADDR:$EXECUTION_BOOTNODE_DISC_PORT"
echo "using bootnode: $ENODE"

echo "Starting geth"
geth \
  --nodekeyhex="522d5e0fd25b33b2d9a28c0376013c3704aa79c1dc5424d107531f22d54f9d58" \
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
  --rpc.allow-unprotected-txs "$MERGE_ARGS" \
  --maxpeers=200 \
  --v5disc \
  --vmodule=rpc=5 
