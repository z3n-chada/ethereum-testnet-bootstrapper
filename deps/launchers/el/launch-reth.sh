#!/bin/bash

env_vars=(
  "EXECUTION_CHECKPOINT_FILE"
  "EXECUTION_CLIENT"
  "EXECUTION_ENGINE_HTTP_PORT"
  "EXECUTION_ENGINE_WS_PORT"
  "EXECUTION_GENESIS_FILE"
  "EXECUTION_HTTP_APIS"
  "EXECUTION_HTTP_PORT"
  "EXECUTION_LAUNCHER"
  "EXECUTION_LOG_LEVEL"
  "EXECUTION_METRIC_PORT"
  "EXECUTION_NODE_DIR"
  "EXECUTION_P2P_PORT"
  "EXECUTION_WS_APIS"
  "EXECUTION_WS_PORT"
  "IP_ADDRESS"
  "IP_SUBNET"
  "JWT_SECRET_FILE"
  "CHAIN_ID"
)

# verify vars we need are set and available.
for var in "${env_vars[@]}" ; do
    if [[ -z "${!var}" ]]; then
        echo "GETH error in geth var check."
        echo "$var not set"
        exit 1
    fi
done


while [ ! -f "$EXECUTION_CHECKPOINT_FILE" ]; do
  echo "Waiting for execution checkpoint file: $EXECUTION_CHECKPOINT_FILE"
    sleep 1
done

# Time for execution clients to start up.
# go geth init
echo "RETH: Init the genesis"
reth init \
    --datadir "$EXECUTION_NODE_DIR" \
    --chain "$EXECUTION_GENESIS_FILE"

reth \
  node \
  --datadir="$EXECUTION_NODE_DIR" \
  --chain "$EXECUTION_GENESIS_FILE" \
  --port "$EXECUTION_P2P_PORT" \
  --discovery.port "$EXECUTION_P2P_PORT" \
  --http --http.api "$EXECUTION_HTTP_APIS" \
  --http.port "$EXECUTION_HTTP_PORT" \
  --http.addr 0.0.0.0 \
  --http.corsdomain "*" \
  --ws --ws.api "$EXECUTION_WS_APIS" \
  --ws.port="$EXECUTION_WS_PORT" \
  --ws.addr 0.0.0.0 \
  --authrpc.port="$EXECUTION_ENGINE_HTTP_PORT" \
  --authrpc.addr=0.0.0.0 \
  --authrpc.jwtsecret="$JWT_SECRET_FILE" \
  --nat "extip:$IP_ADDRESS" \
  --log.persistant --log.directory "$EXECUTION_NODE_DIR/logs/"
