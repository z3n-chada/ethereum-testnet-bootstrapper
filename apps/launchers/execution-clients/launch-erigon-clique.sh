#!/bin/bash

ADDITIONAL_ARGS="--verbosity=$EXECUTION_LOG_LEVEL"

echo "Lauching erigon-execution client"

while [ ! -f "/data/erigon-execution-clients-ready" ]; do
    sleep 1
    echo "Waiting on erigon execution genesis."
done

echo "Detected execution genesis"
static_nodes=`cat /data/execution-enodes.txt`
echo "erigon using static peers: $static_nodes"

if [ ! -f "/data/testnet-resumable" ]; then
    echo "Initing the genesis"
    erigon init \
        --datadir "$EXECUTION_DATA_DIR" \
        "$ERIGON_GENESIS_FILE"
fi

if [ "$IS_MINING" = "true" ]; then
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --mine"
fi

if [ "$TX_FUZZ_ENABLED" = "true" ]; then
    $TX_FUZZ_LAUNCHER &
fi

# geth is either the bootnode, or it should use the bootnode.
if [ -n "$EXECUTION_BOOTNODE_PRIVATE_KEY" ]; then
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --nodekeyhex=$EXECUTION_BOOTNODE_PRIVATE_KEY"
else
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --nodekey=$EXECUTION_DATA_DIR/nodekey.txt"
fi
if [ -n "$EXECUTION_BOOTNODE" ]; then
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --bootnodes=$EXECUTION_BOOTNODE"
fi

echo "Starting erigon with additional args: $ADDITIONAL_ARGS"

echo "execution engine port: $EXECUTION_ENGINE_HTTP_PORT"

erigon \
  --datadir="$EXECUTION_DATA_DIR" \
  --discovery.dns="" \
  --networkid="$NETWORK_ID" \
  --port "$EXECUTION_P2P_PORT" \
  --nat "extip:$IP_ADDR" \
  --http --http.api "$HTTP_APIS" \
  --http.port "$EXECUTION_HTTP_PORT" \
  --http.addr 0.0.0.0 \
  --http.corsdomain "*" \
  --ws \
  --allow-insecure-unlock \
  --netrestrict="$NETRESTRICT_RANGE" \
  --prune=htrc \
  --authrpc.port="$EXECUTION_ENGINE_HTTP_PORT" \
  --authrpc.addr=0.0.0.0 \
  --authrpc.jwtsecret="$JWT_SECRET_FILE" \
  --staticpeers="$static_nodes" $ADDITIONAL_ARGS
