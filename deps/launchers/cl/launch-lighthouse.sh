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

bootnode_enr=`cat $CONSENSUS_BOOTNODE_FILE`

# TODO prometheus
BEACON_NODE_CMD="lighthouse"
BEACON_NODE_CMD+=" beacon_node"
BEACON_NODE_CMD+=" --boot-nodes=$bootnode_enr"
BEACON_NODE_CMD+=" --debug-level=$CONSENSUS_LOG_LEVEL"
BEACON_NODE_CMD+=" --datadir=$CONSENSUS_NODE_DIR"
BEACON_NODE_CMD+=" --testnet-dir=$COLLECTION_DIR"
BEACON_NODE_CMD+=" --disable-enr-auto-update"
BEACON_NODE_CMD+=" --enable-private-discovery"
BEACON_NODE_CMD+=" --enr-address=$IP_ADDRESS"
BEACON_NODE_CMD+=" --enr-udp-port=$CONSENSUS_P2P_PORT"
BEACON_NODE_CMD+=" --enr-tcp-port=$CONSENSUS_P2P_PORT"
BEACON_NODE_CMD+=" --discovery-port=$CONSENSUS_P2P_PORT"
BEACON_NODE_CMD+=" --listen-address=0.0.0.0"
BEACON_NODE_CMD+=" --port=$CONSENSUS_P2P_PORT"
BEACON_NODE_CMD+=" --http"
BEACON_NODE_CMD+=" --http-address=0.0.0.0"
BEACON_NODE_CMD+=" --http-port=$CONSENSUS_BEACON_API_PORT"
BEACON_NODE_CMD+=" --http-allow-sync-stalled"
BEACON_NODE_CMD+=" --http-allow-origin=*"
BEACON_NODE_CMD+=" --disable-packet-filter"
BEACON_NODE_CMD+=" --execution-endpoints=http://127.0.0.1:$CL_EXECUTION_ENGINE_HTTP_PORT"
BEACON_NODE_CMD+=" --jwt-secrets=$JWT_SECRET_FILE"
BEACON_NODE_CMD+=" --suggested-fee-recipient=0x00000000219ab540356cbb839cbe05303d7705fa"
BEACON_NODE_CMD+=" --subscribe-all-subnets"
BEACON_NODE_CMD+=" --metrics"
BEACON_NODE_CMD+=" --metrics-address=0.0.0.0"
BEACON_NODE_CMD+=" --metrics-allow-origin=*"
BEACON_NODE_CMD+=" --metrics-port=$CONSENSUS_BEACON_METRIC_PORT"
# validator args
VALIDATOR_CMD="lighthouse"
VALIDATOR_CMD+=" validator_client"
VALIDATOR_CMD+=" --debug-level=$CONSENSUS_LOG_LEVEL"
VALIDATOR_CMD+=" --testnet-dir=$COLLECTION_DIR"
VALIDATOR_CMD+=" --validators-dir $CONSENSUS_NODE_DIR/keys"
VALIDATOR_CMD+=" --secrets-dir $CONSENSUS_NODE_DIR/secrets"
VALIDATOR_CMD+=" --init-slashing-protection"
VALIDATOR_CMD+=" --http"
VALIDATOR_CMD+=" --unencrypted-http-transport"
VALIDATOR_CMD+=" --http-address=0.0.0.0"
VALIDATOR_CMD+=" --http-port=$CONSENSUS_VALIDATOR_RPC_PORT"
VALIDATOR_CMD+=" --beacon-nodes=http://127.0.0.1:$CONSENSUS_BEACON_API_PORT"
VALIDATOR_CMD+=" --suggested-fee-recipient=0x00000000219ab540356cbb839cbe05303d7705fa"
VALIDATOR_CMD+=" --metrics"
VALIDATOR_CMD+=" --metrics-address=0.0.0.0"
VALIDATOR_CMD+=" --metrics-allow-origin=*"
VALIDATOR_CMD+=" --metrics-port=$CONSENSUS_VALIDATOR_METRIC_PORT"
VALIDATOR_CMD+=" --graffiti=$CONSENSUS_GRAFFITI"


if [ "$IS_DENEB" == 1 ]; then
BEACON_NODE_CMD+=" --trusted-setup-file-override=$TRUSTED_SETUP_JSON_FILE"
#BEACON_NODE_CMD+=" --self-limiter=blob_sidecars_by_range:512/10"
fi

echo "Launching lighthouse beacon-node."
eval "$BEACON_NODE_CMD" &

sleep 10

echo "Launching lighthouse validator client"
eval "$VALIDATOR_CMD"
