#!/bin/bash

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

BEACON_NODE_CMD="nimbus_beacon_node"
BEACON_NODE_CMD+=" --non-interactive"
BEACON_NODE_CMD+=" --bootstrap-node=$bootnode_enr"
BEACON_NODE_CMD+=" --log-level=$CONSENSUS_LOG_LEVEL"
BEACON_NODE_CMD+=" --udp-port=$CONSENSUS_P2P_PORT"
BEACON_NODE_CMD+=" --tcp-port=$CONSENSUS_P2P_PORT"
BEACON_NODE_CMD+=" --network=$COLLECTION_DIR/"
BEACON_NODE_CMD+=" --data-dir=$CONSENSUS_NODE_DIR"
BEACON_NODE_CMD+=" --web3-url=http://127.0.0.1:$CL_EXECUTION_ENGINE_HTTP_PORT"
BEACON_NODE_CMD+=" --nat=extip:$IP_ADDRESS"
BEACON_NODE_CMD+=" --enr-auto-update=false"
BEACON_NODE_CMD+=" --rest"
BEACON_NODE_CMD+=" --rest-address=0.0.0.0"
BEACON_NODE_CMD+=" --rest-allow-origin=*"
BEACON_NODE_CMD+=" --rest-port=$CONSENSUS_BEACON_API_PORT"
BEACON_NODE_CMD+=" --doppelganger-detection=false"
BEACON_NODE_CMD+=" --subscribe-all-subnets=true"
BEACON_NODE_CMD+=" --jwt-secret=$JWT_SECRET_FILE"
BEACON_NODE_CMD+=" --metrics"
BEACON_NODE_CMD+=" --metrics-address=0.0.0.0"
BEACON_NODE_CMD+=" --metrics-port=$CONSENSUS_BEACON_METRIC_PORT"
BEACON_NODE_CMD+=" --in-process-validators=true"
BEACON_NODE_CMD+=" --secrets-dir=$CONSENSUS_NODE_DIR/secrets"
BEACON_NODE_CMD+=" --validators-dir=$CONSENSUS_NODE_DIR/keys"
BEACON_NODE_CMD+=" --suggested-fee-recipient=0x00000000219ab540356cbb839cbe05303d7705fa"
BEACON_NODE_CMD+=" --graffiti=$CONSENSUS_GRAFFITI"
BEACON_NODE_CMD+=" --insecure-netkey-password"
BEACON_NODE_CMD+=" --netkey-file=$CONSENSUS_NODE_DIR/netkey-file.txt"
#BEACON_NODE_CMD+=" --dump:on"
#BEACON_NODE_CMD+=" --num-threads=4"
#BEACON_NODE_CMD+=" --history=prune"

echo "Launching nimbus beacon-node + validator."
eval "$BEACON_NODE_CMD"
