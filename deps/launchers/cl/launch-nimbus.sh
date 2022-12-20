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
        echo "NIMBUS error in geth var check."
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

echo "Launching nimbus."
##nimbus_beacon_node \
##    --non-interactive \
##    --data-dir="$NODE_DIR" \
##    --log-file="$NODE_DIR/beacon-log.txt" \
##    --network="$TESTNET_DIR" \
##    --secrets-dir="$NODE_DIR/secrets" \
##    --validators-dir="$NODE_DIR/keys" \
##    --rest \
##    --rest-address="0.0.0.0" --rest-port="$BEACON_API_PORT" \
##    --listen-address="$IP_ADDR" \
##    --tcp-port="$CONSENSUS_P2P_PORT" \
##    --udp-port="$CONSENSUS_P2P_PORT" \
##    --nat="extip:$IP_ADDR" \
##    --discv5=true \
##    --subscribe-all-subnets \
##    --insecure-netkey-password \
##    --netkey-file="$NODE_DIR/netkey-file.txt" \
##    --graffiti="nimbus-kilnv2:$IP_ADDR" \
##    --in-process-validators=true \
##    --doppelganger-detection=true \
##    --bootstrap-node="$bootnode_enr" \
##    --jwt-secret="$JWT_SECRET_FILE" \
##    --web3-url=http://"$HTTP_WEB3_IP_ADDR:$EXECUTION_ENGINE_HTTP_PORT" \
##    --terminal-total-difficulty-override="$TERMINAL_TOTAL_DIFFICULTY" \
##    --dump \
##    --log-level="$NIMBUS_DEBUG_LEVEL"
