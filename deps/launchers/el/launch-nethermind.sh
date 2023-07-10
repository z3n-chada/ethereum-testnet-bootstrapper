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
        echo "NETHERMIND error in geth var check."
        echo "$var not set"
        exit 1
    fi
done


while [ ! -f "$EXECUTION_CHECKPOINT_FILE" ]; do
  echo "Waiting for execution checkpoint file: $EXECUTION_CHECKPOINT_FILE"
    sleep 1
done


echo "{}" > /tmp/nethermind.cfg
# --Init.KzgSetupFile "$TRUSTED_SETUP_TXT_FILE" \
nethermind \
  --config="/tmp/nethermind.cfg" \
  --datadir="$EXECUTION_NODE_DIR" \
  --Init.ChainSpecPath="$EXECUTION_GENESIS_FILE" \
  --Init.StoreReceipts=true \
  --Init.WebSocketsEnabled=true \
  --Init.EnableUnsecuredDevWallet=true \
  --Init.DiagnosticMode="None" \
  --JsonRpc.Enabled=true \
  --JsonRpc.EnabledModules="$EXECUTION_HTTP_APIS" \
  --JsonRpc.Port="$EXECUTION_HTTP_PORT" \
  --JsonRpc.WebSocketsPort="$EXECUTION_WS_PORT" \
  --JsonRpc.Host=0.0.0.0 \
  --Network.ExternalIp="$IP_ADDRESS" \
  --Network.LocalIp="$IP_ADDRESS" \
  --Network.DiscoveryPort="$EXECUTION_P2P_PORT" \
  --Network.P2PPort="$EXECUTION_P2P_PORT" \
  --JsonRpc.JwtSecretFile="$JWT_SECRET_FILE" \
  --JsonRpc.AdditionalRpcUrls="http://localhost:$EXECUTION_ENGINE_HTTP_PORT|http|net;eth;subscribe;engine;web3;client;clique,http://localhost:$EXECUTION_ENGINE_WS_PORT|ws|net;eth;subscribe;engine;web3;client"
