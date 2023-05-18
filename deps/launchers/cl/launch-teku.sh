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
        echo "TEKU error in geth var check."
        echo "$var not set"
        exit 1
    fi
done

# we can wait for the bootnode enr to drop before we get the signal to start up.
while [ ! -f "$CONSENSUS_BOOTNODE_FILE" ]; do
  echo "consensus client waiting for bootnode enr file: $CONSENSUS_BOOTNODE_FILE"
  sleep 1
done

bootnode_enr=`cat $CONSENSUS_BOOTNODE_FILE`

while [ ! -f "$CONSENSUS_CHECKPOINT_FILE" ]; do
  echo "Waiting for consensus checkpoint file: $CONSENSUS_CHECKPOINT_FILE"
    sleep 1
done


bootnode_enr=`cat $CONSENSUS_BOOTNODE_FILE`

teku \
    --logging="$CONSENSUS_LOG_LEVEL" \
    --log-color-enabled=false \
    --log-destination=CONSOLE \
    --network="$TESTNET_DIR/config.yaml" \
    --initial-state="$TESTNET_DIR/genesis.ssz" \
    --data-path="$CONSENSUS_NODE_DIR" \
    --data-storage-mode=PRUNE \
    --p2p-enabled=true \
    --p2p-advertised-ip="$IP_ADDRESS" \
    --p2p-advertised-port="$CONSENSUS_P2P_PORT" \
    --p2p-advertised-udp-port="$CONSENSUS_P2P_PORT" \
    --p2p-discovery-enabled=true \
    --p2p-peer-lower-bound=1 \
    --p2p-port="$CONSENSUS_P2P_PORT" \
    --p2p-peer-upper-bound="$NUM_CLIENT_NODES" \
    --p2p-discovery-bootnodes="$bootnode_enr" \
    --p2p-subscribe-all-subnets-enabled=true \
    --metrics-enabled=true \
    --metrics-interface=0.0.0.0 \
    --metrics-port="$CONSENSUS_BEACON_METRIC_PORT" \
    --rest-api-enabled=true \
    --rest-api-docs-enabled=true \
    --rest-api-interface=0.0.0.0 \
    --rest-api-port="$CONSENSUS_BEACON_API_PORT" \
    --metrics-host-allowlist="*" \
    --rest-api-host-allowlist="*" \
    --data-storage-non-canonical-blocks-enabled=true \
    --validators-graffiti="$CONSENSUS_GRAFFITI" \
    --validator-keys="$CONSENSUS_NODE_DIR/keys:$CONSENSUS_NODE_DIR/secrets" \
    --validators-keystore-locking-enabled=false \
    --ee-endpoint="http://127.0.0.1:$EXECUTION_ENGINE_HTTP_PORT" \
    --validators-proposer-default-fee-recipient=0xA18Fd83a55A9BEdB96d66C24b768259eED183be3 \
    --ee-jwt-secret-file="$JWT_SECRET_FILE"

#    --p2p-discovery-site-local-addresses-enabled=true \