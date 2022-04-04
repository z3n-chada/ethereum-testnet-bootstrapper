#!/bin/bash

env_vars=( "BOOTNODE_ENR" "EXECUTION_DATA_DIR" "GETH_EXECUTION_GENESIS" "NETWORK_ID" "EXECUTION_P2P_PORT" "EXECUTION_HTTP_PORT" "EXECUTION_WS_PORT" "HTTP_APIS" "WS_APIS" "IP_ADDR" "NETRESTRICT_RANGE" "END_FORK_NAME" "GETH_GENESIS_FILE" "EXECUTION_LOG_LEVEL")

for var in "${env_vars[@]}" ; do
    if [[ -z "$var" ]]; then
        echo "$var not set"
        exit 1
    fi
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
    echo "Geth is overriding terminaltotaldifficulty"
else
    echo "Geth not overriding terminal total difficulty. Got an END_FORK:$END_FORK_NAME"
    echo "if you are trying to test a merge configuration check that the config file is sane"
fi 

echo "Lauching execution client"

echo "testnet-password" > /data/geth-account-passwords.txt

while [ ! -f "/data/execution-clients-ready" ]; do
    sleep 1
    echo "Waiting on exeuction genesis"
done

echo "Detected execution genesis"

echo "Initing the genesis"
geth init \
    --datadir "$EXECUTION_DATA_DIR" \
    "$GETH_GENESIS_FILE"

if [ -n "$JWT_SECRET_FILE" ]; then
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --authrpc.port=$EXECUTION_ENGINE_AUTH_PORT --authrpc.addr=0.0.0.0 --authrpc.vhosts=\"*\" --authrpc.jwtsecret=$JWT_SECRET_FILE"
    echo "Geth is using JWT"
fi

echo "Starting geth"

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
  --rpc.allow-unprotected-txs $ADDITIONAL_ARGS \
  --allow-insecure-unlock \
  --maxpeers=200 \
  --syncmode=full \
  --vmodule=rpc=5 

  # --v5disc \
