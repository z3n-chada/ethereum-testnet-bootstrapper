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
  "IS_DENEB"
)

# verify vars we need are set and available.
for var in "${env_vars[@]}" ; do
    if [[ -z "${!var}" ]]; then
        echo "BESU error in geth var check."
        echo "$var not set"
        exit 1
    fi
done


while [ ! -f "$EXECUTION_CHECKPOINT_FILE" ]; do
  echo "Waiting for execution checkpoint file: $EXECUTION_CHECKPOINT_FILE"
    sleep 1
done

if [ "$IS_DENEB" == 1 ]; then
  echo "Launching deneb ready besu."
  besu \
    --logging="$EXECUTION_LOG_LEVEL" \
    --bootnodes="$EXECUTION_BOOTNODE" \
    --data-path="$EXECUTION_DATA_DIR" \
    --genesis-file="$EXECUTION_GENESIS_FILE" \
    --network-id="$NETWORK_ID" \
    --rpc-http-enabled=true --rpc-http-api="$EXECUTION_HTTP_APIS" \
    --rpc-http-host=0.0.0.0 \
    --rpc-http-port="$EXECUTION_HTTP_PORT" \
    --rpc-http-cors-origins="*" \
    --rpc-ws-enabled=true --rpc-ws-api="$EXECUTION_WS_APIS" \
    --rpc-ws-host=0.0.0.0 \
    --rpc-ws-port="$EXECUTION_WS_PORT" \
    --host-allowlist="*" \
    --p2p-enabled=true \
    --p2p-host="$IP_ADDRESS" \
    --nat-method=DOCKER \
    --sync-mode=FULL \
    --p2p-port="$EXECUTION_P2P_PORT" \
    --engine-rpc-enabled=true \
    --engine-jwt-enabled \
    --engine-jwt-secret="$JWT_SECRET_FILE" \
    --engine-host-allowlist="*" \
    --data-storage-format="BONSAI" \
    --kzg-trusted-setup="$TRUSTED_SETUP_TXT_FILE" \
    --engine-rpc-port="$EXECUTION_ENGINE_HTTP_PORT"
else
    besu \
    --logging="$EXECUTION_LOG_LEVEL" \
    --bootnodes="$EXECUTION_BOOTNODE" \
    --data-path="$EXECUTION_DATA_DIR" \
    --genesis-file="$EXECUTION_GENESIS_FILE" \
    --network-id="$NETWORK_ID" \
    --rpc-http-enabled=true --rpc-http-api="$EXECUTION_HTTP_APIS" \
    --rpc-http-host=0.0.0.0 \
    --rpc-http-port="$EXECUTION_HTTP_PORT" \
    --rpc-http-cors-origins="*" \
    --rpc-ws-enabled=true --rpc-ws-api="$EXECUTION_WS_APIS" \
    --rpc-ws-host=0.0.0.0 \
    --rpc-ws-port="$EXECUTION_WS_PORT" \
    --host-allowlist="*" \
    --p2p-enabled=true \
    --p2p-host="$IP_ADDRESS" \
    --nat-method=DOCKER \
    --sync-mode=FULL \
    --p2p-port="$EXECUTION_P2P_PORT" \
    --engine-rpc-enabled=true \
    --engine-jwt-enabled \
    --engine-jwt-secret="$JWT_SECRET_FILE" \
    --engine-host-allowlist="*" \
    --data-storage-format="BONSAI" \
    --engine-rpc-port="$EXECUTION_ENGINE_HTTP_PORT"
fi