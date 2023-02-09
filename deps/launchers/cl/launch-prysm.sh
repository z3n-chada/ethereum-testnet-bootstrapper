#!/bin/bash

env_vars=(
  "CONSENSUS_BEACON_API_PORT"
  "CONSENSUS_BEACON_METRIC_PORT"
  "CONSENSUS_BEACON_RPC_PORT"
  "CONSENSUS_BOOTNODE_FILE"
  "CONSENSUS_CHECKPOINT_FILE"
  "CONSENSUS_CLIENT"
  "CONSENSUS_CONFIG_FILE"
  "CONSENSUS_GENESIS_FILE"
  "CONSENSUS_GRAFFITI"
  "CONSENSUS_NODE_DIR"
  "CONSENSUS_P2P_PORT"
  "CONSENSUS_VALIDATOR_METRIC_PORT"
  "CONSENSUS_VALIDATOR_RPC_PORT"
  "CONSENSUS_LOG_LEVEL"
  "IP_ADDRESS"
  "IP_SUBNET"
  "JWT_SECRET_FILE"
  "TESTNET_DIR"
  "NUM_CLIENT_NODES"
  "EXECUTION_ENGINE_HTTP_PORT"
  "EXECUTION_ENGINE_WS_PORT"
)
# verify vars we need are set and available.
for var in "${env_vars[@]}" ; do
    if [[ -z "${!var}" ]]; then
        echo "PRYSM error in geth var check."
        echo "$var not set"
        exit 1
    fi
done

# we can wait for the bootnode enr to drop before we get the signal to start up.
while [ ! -f "$CONSENSUS_BOOTNODE_FILE" ]; do
  echo "consensus client waiting for bootnode enr file: $CONSENSUS_BOOTNODE_FILE"
  sleep 1
done

while [ ! -f "$CONSENSUS_CHECKPOINT_FILE" ]; do
  echo "Waiting for consensus checkpoint file: $CONSENSUS_CHECKPOINT_FILE"
    sleep 1
done

beacon-chain \
  --log-file="$CONSENSUS_NODE_DIR/beacon.log" \
  --accept-terms-of-use=true \
  --datadir="$CONSENSUS_NODE_DIR" \
  --chain-config-file="$TESTNET_DIR/config.yaml" \
  --genesis-state="$TESTNET_DIR/genesis.ssz" \
  --bootstrap-node="$(< "$CONSENSUS_BOOTNODE_FILE")" \
  --verbosity="$CONSENSUS_LOG_LEVEL" \
  --p2p-host-ip="$IP_ADDRESS" \
  --p2p-max-peers="$NUM_CLIENT_NODES" \
  --p2p-udp-port="$CONSENSUS_P2P_PORT" --p2p-tcp-port="$CONSENSUS_P2P_PORT" \
  --monitoring-host=0.0.0.0 --monitoring-port="$CONSENSUS_BEACON_METRIC_PORT" \
  --rpc-host=0.0.0.0 --rpc-port="$CONSENSUS_BEACON_RPC_PORT" \
  --grpc-gateway-host=0.0.0.0 \
  --grpc-gateway-port="$CONSENSUS_BEACON_API_PORT" \
  --enable-debug-rpc-endpoints \
  --p2p-allowlist="$IP_SUBNET" \
  --subscribe-all-subnets \
  --force-clear-db \
  --jwt-secret="$JWT_SECRET_FILE" \
  --suggested-fee-recipient=0x00000000219ab540356cbb839cbe05303d7705fa \
  --execution-endpoint="http://127.0.0.1:$EXECUTION_ENGINE_HTTP_PORT" \
  --min-sync-peers 1 &

sleep 10

validator \
  --log-file="$CONSENSUS_NODE_DIR/validator.log" \
  --accept-terms-of-use=true \
  --datadir="$CONSENSUS_NODE_DIR" \
  --chain-config-file="$TESTNET_DIR/config.yaml" \
  --beacon-rpc-provider="127.0.0.1:$CONSENSUS_BEACON_RPC_PORT" \
  --monitoring-host=0.0.0.0 --monitoring-port="$CONSENSUS_VALIDATOR_METRIC_PORT" \
  --graffiti="$CONSENSUS_GRAFFITI" \
  --wallet-dir="$CONSENSUS_NODE_DIR" \
  --wallet-password-file="$CONSENSUS_NODE_DIR/wallet-password.txt" \
  --suggested-fee-recipient=0x00000000219ab540356cbb839cbe05303d7705fa \
  --verbosity=debug
