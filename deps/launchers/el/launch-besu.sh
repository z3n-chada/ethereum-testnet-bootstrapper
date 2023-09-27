#!/bin/bash

while [ ! -f "$EXECUTION_CHECKPOINT_FILE" ]; do
  echo "Waiting for execution checkpoint file: $EXECUTION_CHECKPOINT_FILE"
    sleep 1
done

if [ "$RUN_JSON_RPC_SNOOPER" == "true" ]; then
  echo "Launching json_rpc_snoop."
  json_rpc_snoop -p "$CL_EXECUTION_ENGINE_HTTP_PORT" http://localhost:"$EXECUTION_ENGINE_HTTP_PORT" 2>&1 | tee "$EXECUTION_NODE_DIR/json_rpc_snoop.log" &
fi

EXECUTION_CMD="besu"
EXECUTION_CMD+=" --logging=$EXECUTION_LOG_LEVEL"
EXECUTION_CMD+=" --data-path=$EXECUTION_DATA_DIR"
EXECUTION_CMD+=" --genesis-file=$EXECUTION_GENESIS_FILE"
EXECUTION_CMD+=" --network-id=$NETWORK_ID"
EXECUTION_CMD+=" --host-allowlist=*"
EXECUTION_CMD+=" --rpc-http-enabled=true"
EXECUTION_CMD+=" --rpc-http-host=0.0.0.0"
EXECUTION_CMD+=" --rpc-http-port=$EXECUTION_HTTP_PORT"
EXECUTION_CMD+=" --rpc-http-api=$EXECUTION_HTTP_APIS"
EXECUTION_CMD+=" --rpc-http-cors-origins=*"
EXECUTION_CMD+=" --rpc-ws-enabled=true"
EXECUTION_CMD+=" --rpc-ws-host=0.0.0.0"
EXECUTION_CMD+=" --rpc-ws-port=$EXECUTION_WS_PORT"
EXECUTION_CMD+=" --rpc-ws-api=$EXECUTION_WS_APIS"
EXECUTION_CMD+=" --p2p-enabled=true"
EXECUTION_CMD+=" --p2p-host=$IP_ADDRESS"
EXECUTION_CMD+=" --p2p-port=$EXECUTION_P2P_PORT"
EXECUTION_CMD+=" --engine-rpc-enabled=true"
EXECUTION_CMD+=" --engine-jwt-secret=$JWT_SECRET_FILE"
EXECUTION_CMD+=" --engine-host-allowlist=*"
EXECUTION_CMD+=" --engine-rpc-port=$EXECUTION_ENGINE_HTTP_PORT"
EXECUTION_CMD+=" --sync-mode=FULL"
EXECUTION_CMD+=" --data-storage-format=BONSAI"
EXECUTION_CMD+=" --metrics-enabled=true"
EXECUTION_CMD+=" --metrics-host=0.0.0.0"
EXECUTION_CMD+=" --metrics-port=$EXECUTION_METRIC_PORT"
#EXECUTION_CMD+=" --nat-method=DOCKER"

if [ "$IS_DENEB" == 1 ]; then
EXECUTION_CMD+=" --kzg-trusted-setup=$TRUSTED_SETUP_TXT_FILE"
fi

echo "Launching besu execution client."
eval "$EXECUTION_CMD"