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

# by this time we can be sure the bootnode file has been completely written.
bootnode_enr=`cat $CONSENSUS_BOOTNODE_FILE`

echo "Launching teku beacon-node + validator."

BEACON_NODE_CMD="teku"
BEACON_NODE_CMD+=" --p2p-discovery-bootnodes=$bootnode_enr"
BEACON_NODE_CMD+=" --logging=$CONSENSUS_LOG_LEVEL"
BEACON_NODE_CMD+=" --log-destination=CONSOLE"
BEACON_NODE_CMD+=" --network=$CONSENSUS_CONFIG_FILE"
BEACON_NODE_CMD+=" --initial-state=$CONSENSUS_GENESIS_FILE"
BEACON_NODE_CMD+=" --data-path=$CONSENSUS_NODE_DIR"
BEACON_NODE_CMD+=" --data-storage-mode=PRUNE"
BEACON_NODE_CMD+=" --p2p-enabled=true"
BEACON_NODE_CMD+=" --p2p-subscribe-all-subnets-enabled=true"
BEACON_NODE_CMD+=" --p2p-peer-lower-bound=1"
BEACON_NODE_CMD+=" --p2p-advertised-ip=$IP_ADDRESS"
BEACON_NODE_CMD+=" --p2p-discovery-site-local-addresses-enabled=true"
BEACON_NODE_CMD+=" --rest-api-enabled=true"
BEACON_NODE_CMD+=" --rest-api-docs-enabled=true"
BEACON_NODE_CMD+=" --rest-api-interface=0.0.0.0"
BEACON_NODE_CMD+=" --rest-api-port=$CONSENSUS_BEACON_API_PORT"
BEACON_NODE_CMD+=" --rest-api-host-allowlist='*'"
BEACON_NODE_CMD+=" --data-storage-non-canonical-blocks-enabled=true"
BEACON_NODE_CMD+=" --ee-jwt-secret-file=$JWT_SECRET_FILE"
BEACON_NODE_CMD+=" --ee-endpoint=http://127.0.0.1:$CL_EXECUTION_ENGINE_HTTP_PORT"
BEACON_NODE_CMD+=" --metrics-enabled"
BEACON_NODE_CMD+=" --metrics-interface=0.0.0.0"
BEACON_NODE_CMD+=" --metrics-host-allowlist='*'"
BEACON_NODE_CMD+=" --metrics-categories=BEACON,PROCESS,LIBP2P,JVM,NETWORK,PROCESS"
BEACON_NODE_CMD+=" --metrics-port=$CONSENSUS_BEACON_METRIC_PORT"
BEACON_NODE_CMD+=" --validators-graffiti=$CONSENSUS_GRAFFITI"
BEACON_NODE_CMD+=" --validator-keys=$CONSENSUS_NODE_DIR/keys:$CONSENSUS_NODE_DIR/secrets"
BEACON_NODE_CMD+=" --validators-keystore-locking-enabled=false"
BEACON_NODE_CMD+=" --validators-proposer-default-fee-recipient=0x00000000219ab540356cbb839cbe05303d7705fa"

if [ "$IS_DENEB" == 1 ]; then
BEACON_NODE_CMD+=" --Xmetrics-blob-sidecars-storage-enabled=true"
BEACON_NODE_CMD+=" --Xtrusted-setup=$TRUSTED_SETUP_TXT_FILE"
fi

echo "Launching teku beacon-node + validator"
echo "$BEACON_NODE_CMD"
eval "$BEACON_NODE_CMD"