#!/bin/bash

# we can wait for the bootnode enr to drop before we get the signal to start up.
while [ ! -f "$CONSENSUS_BOOTNODE_FILE" ]; do
  echo "consensus client waiting for bootnode enr file: $CONSENSUS_BOOTNODE_FILE"
  sleep 1
done

while [ ! -f "$CONSENSUS_CHECKPOINT_FILE" ]; do
  echo "Waiting for consensus checkpoint file: $CONSENSUS_CHECKPOINT_FILE"
    sleep 1
done

BEACON_NODE_CMD="beacon-chain"
BEACON_NODE_CMD+=" --accept-terms-of-use=true"
BEACON_NODE_CMD+=" --bootstrap-node=$(< "$CONSENSUS_BOOTNODE_FILE")"
BEACON_NODE_CMD+=" --datadir=$CONSENSUS_NODE_DIR"
BEACON_NODE_CMD+=" --chain-config-file=$CONSENSUS_CONFIG_FILE"
BEACON_NODE_CMD+=" --genesis-state=$CONSENSUS_GENESIS_FILE"
BEACON_NODE_CMD+=" --execution-endpoint=http://127.0.0.1:$CL_EXECUTION_ENGINE_HTTP_PORT"
BEACON_NODE_CMD+=" --rpc-host=0.0.0.0"
BEACON_NODE_CMD+=" --rpc-port=$CONSENSUS_BEACON_RPC_PORT"
BEACON_NODE_CMD+=" --grpc-gateway-host=0.0.0.0"
BEACON_NODE_CMD+=" --grpc-gateway-corsdomain=*"
BEACON_NODE_CMD+=" --grpc-gateway-port=$CONSENSUS_BEACON_API_PORT"
BEACON_NODE_CMD+=" --p2p-host-ip=$IP_ADDRESS"
BEACON_NODE_CMD+=" --p2p-tcp-port=$CONSENSUS_P2P_PORT"
BEACON_NODE_CMD+=" --p2p-udp-port=$CONSENSUS_P2P_PORT"
BEACON_NODE_CMD+=" --p2p-static-id=true"
BEACON_NODE_CMD+=" --min-sync-peers=1"
BEACON_NODE_CMD+=" --verbosity=$CONSENSUS_LOG_LEVEL"
BEACON_NODE_CMD+=" --suggested-fee-recipient=0x00000000219ab540356cbb839cbe05303d7705fa"
BEACON_NODE_CMD+=" --subscribe-all-subnets=true"
BEACON_NODE_CMD+=" --jwt-secret=$JWT_SECRET_FILE"
BEACON_NODE_CMD+=" --disable-monitoring=false"
BEACON_NODE_CMD+=" --monitoring-host=0.0.0.0"
BEACON_NODE_CMD+=" --monitoring-port=$CONSENSUS_BEACON_METRIC_PORT"
#BEACON_NODE_CMD+=" --slots-per-archive-point=32"

VALIDATOR_CMD="validator"
VALIDATOR_CMD+=" --accept-terms-of-use=true"
VALIDATOR_CMD+=" --chain-config-file=$CONSENSUS_CONFIG_FILE"
VALIDATOR_CMD+=" --beacon-rpc-gateway-provider=127.0.0.1:$CONSENSUS_BEACON_API_PORT"
VALIDATOR_CMD+=" --beacon-rpc-provider=127.0.0.1:$CONSENSUS_BEACON_RPC_PORT"
VALIDATOR_CMD+=" --wallet-dir=$CONSENSUS_NODE_DIR"
VALIDATOR_CMD+=" --wallet-password-file=$CONSENSUS_NODE_DIR/wallet-password.txt"
VALIDATOR_CMD+=" --datadir=$CONSENSUS_NODE_DIR"
VALIDATOR_CMD+=" --verbosity=$CONSENSUS_LOG_LEVEL"
VALIDATOR_CMD+=" --suggested-fee-recipient=0x00000000219ab540356cbb839cbe05303d7705fa"
VALIDATOR_CMD+=" --graffiti=$CONSENSUS_GRAFFITI"
VALIDATOR_CMD+=" --disable-monitoring=false"
VALIDATOR_CMD+=" --monitoring-host=0.0.0.0"
VALIDATOR_CMD+=" --monitoring-port=$CONSENSUS_VALIDATOR_METRIC_PORT"


echo "Launching prysm beacon-node."
eval "$BEACON_NODE_CMD" &

sleep 10

echo "Launching pyrsm validator."
eval "$VALIDATOR_CMD"