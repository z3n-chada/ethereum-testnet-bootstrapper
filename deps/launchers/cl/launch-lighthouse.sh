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
  "COLLECTION_DIR"
  "NUM_CLIENT_NODES"
  "EXECUTION_ENGINE_HTTP_PORT"
  "EXECUTION_ENGINE_WS_PORT"
)
# verify vars we need are set and available.
for var in "${env_vars[@]}" ; do
    if [[ -z "${!var}" ]]; then
        echo "Lighthouse error in geth var check."
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

bootnode_enr=`cat $CONSENSUS_BOOTNODE_FILE`

echo "Launching lighthouse."

lighthouse \
      --testnet-dir="$COLLECTION_DIR" \
      -l \
      bn \
      --datadir="$CONSENSUS_NODE_DIR" \
      --staking \
      --http-address=0.0.0.0 \
      --http-port="$CONSENSUS_BEACON_API_PORT" \
      --http-allow-origin="*" \
      --http-allow-sync-stalled \
      --listen-address=0.0.0.0 \
      --port="$CONSENSUS_P2P_PORT" \
      --execution-endpoints="http://127.0.0.1:$EXECUTION_ENGINE_HTTP_PORT" \
      --enable-private-discovery \
      --enr-address "$IP_ADDRESS" \
      --enr-udp-port "$CONSENSUS_P2P_PORT" \
      --enr-tcp-port "$CONSENSUS_P2P_PORT" \
      --discovery-port "$CONSENSUS_P2P_PORT" \
      --jwt-secrets="$JWT_SECRET_FILE" \
      --boot-nodes="$bootnode_enr" \
      --target-peers="$NUM_CLIENT_NODES" \
      --subscribe-all-subnets \
      --debug-level="$CONSENSUS_LOG_LEVEL" \
      --suggested-fee-recipient=0x00000000219ab540356cbb839cbe05303d7705fa &

sleep 10
lighthouse \
      -l \
      --testnet-dir="$COLLECTION_DIR" \
      vc \
      --validators-dir "$CONSENSUS_NODE_DIR/keys" \
      --secrets-dir "$CONSENSUS_NODE_DIR/secrets" \
      --init-slashing-protection \
      --beacon-nodes="http://127.0.0.1:$CONSENSUS_BEACON_API_PORT" \
      --graffiti="$CONSENSUS_GRAFFITI" \
      --http --http-port="$CONSENSUS_VALIDATOR_RPC_PORT" \
      --suggested-fee-recipient=0x00000000219ab540356cbb839cbe05303d7705fa \
      --debug-level="$CONSENSUS_LOG_LEVEL" \
      --logfile="$CONSENSUS_NODE_DIR/validator.log" --logfile-debug-level="$CONSENSUS_LOG_LEVEL"
