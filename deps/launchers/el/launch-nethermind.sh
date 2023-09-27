#!/bin/bash

while [ ! -f "$EXECUTION_CHECKPOINT_FILE" ]; do
  echo "Waiting for execution checkpoint file: $EXECUTION_CHECKPOINT_FILE"
    sleep 1
done

if [ "$RUN_JSON_RPC_SNOOPER" == "true" ]; then
  echo "Launching json_rpc_snoop"
  json_rpc_snoop -p "$CL_EXECUTION_ENGINE_HTTP_PORT" http://localhost:"$EXECUTION_ENGINE_HTTP_PORT" 2>&1 | tee "$EXECUTION_NODE_DIR/json_rpc_snoop.log" &
fi

echo "{}" > /tmp/none.cfg
EXECUTION_CMD="nethermind"
EXECUTION_CMD+=" --log=$EXECUTION_LOG_LEVEL"
EXECUTION_CMD+=" --datadir=$EXECUTION_NODE_DIR"
EXECUTION_CMD+=" --Init.ChainSpecPath=$EXECUTION_GENESIS_FILE"
EXECUTION_CMD+=" --Init.WebSocketsEnabled=true"
EXECUTION_CMD+=" --config=/tmp/none.cfg"
EXECUTION_CMD+=" --JsonRpc.Enabled=true"
EXECUTION_CMD+=" --JsonRpc.EnabledModules=$EXECUTION_HTTP_APIS"
EXECUTION_CMD+=" --JsonRpc.Host=0.0.0.0"
EXECUTION_CMD+=" --JsonRpc.Port=$EXECUTION_HTTP_PORT"
EXECUTION_CMD+=" --JsonRpc.WebSocketsPort=$EXECUTION_WS_PORT"
EXECUTION_CMD+=" --JsonRpc.EngineHost=0.0.0.0"
EXECUTION_CMD+=" --JsonRpc.EnginePort=$EXECUTION_ENGINE_HTTP_PORT"
EXECUTION_CMD+=" --Network.LocalIp=$IP_ADDRESS"
EXECUTION_CMD+=" --Network.ExternalIp=$IP_ADDRESS"
EXECUTION_CMD+=" --Network.DiscoveryPort=$EXECUTION_P2P_PORT"
EXECUTION_CMD+=" --Network.P2PPort=$EXECUTION_P2P_PORT"
EXECUTION_CMD+=" --JsonRpc.JwtSecretFile=$JWT_SECRET_FILE"
EXECUTION_CMD+=" --Metrics.Enabled=true"
EXECUTION_CMD+=" --Metrics.ExposePort=$EXECUTION_METRIC_PORT"

if [ "$IS_DENEB" == 1 ]; then
EXECUTION_CMD+=" --Init.KzgSetupPath=$TRUSTED_SETUP_TXT_FILE"
fi

echo "Launching nethermind execution client"
eval "$EXECUTION_CMD"