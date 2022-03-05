#!/bin/bash

env_vars=( "BOOTNODE_ENR" "EXECUTION_DATA_DIR" "EXECUTION_GENESIS" "NETWORK_ID" "EXECUTION_P2P_PORT" "EXECUTION_HTTP_PORT" "EXECUTION_WS_PORT" "HTTP_APIS" "WS_APIS" "IP_ADDR" "NETRESTRICT_RANGE" "END_FORK")

for var in "${env_vars[@]}" ; do
    if [[ -z "$var" ]]; then
        echo "$var not set"
        exit 1
    fi
done

echo "geth got a valid env-var set"

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
ENODES=`cat /data/local_testnet/execution-bootstrapper/enodes.txt | tr -d "\n"`
echo $ENODES
echo "Initing the genesis"
geth init \
    --datadir "$EXECUTION_DATA_DIR" \
    "$EXECUTION_GENESIS"

echo "Starting geth"

geth \
  --bootnodes "$ENODES" \
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
  --rpc.allow-unprotected-txs "$MERGE_ARGS" \
  --vmodule=rpc=5 

