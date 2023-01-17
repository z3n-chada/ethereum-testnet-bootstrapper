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
        echo "LODESTAR error in geth var check."
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

echo "Launching Lodestar."

lodestar beacon \
    --rootDir="$NODE_DIR" \
    --configFile="$TESTNET_DIR/config.yaml" \
    --paramsFile="$TESTNET_DIR/config.yaml" \
    --genesisStateFile="$TESTNET_DIR/genesis.ssz" \
    --execution.urls="http://127.0.0.1:$EXECUTION_ENGINE_HTTP_PORT" \
    --jwt-secret="$JWT_SECRET_FILE" \
    --network.discv5.bootEnrs="$bootnode_enr" \
    --api.rest.enabled=true \
    --api.rest.host=0.0.0.0 \
    --api.rest.port="$CONSENSUS_BEACON_API_PORT" \
    --api.rest.api="*" \
    --logLevel="$LSTAR_DEBUG_LEVEL" \
    --logLevelFile=debug \
    --logFile="$CONSENSUS_NODE_DIR/beacon.log" \
    --logRotate \
    --chain.defaultFeeRecipient=0x00000000219ab540356cbb839cbe05303d7705fa &

sleep 10

lodestar validator \
    --rootDir="$CONSENSUS_NODE_DIR" \
    --paramsFile="$TESTNET_DIR/config.yaml" \
    --keystoresDir="$CONSENSUS_NODE_DIR/keys/" \
    --secretsDir="$CONSENSUS_NODE_DIR/secrets/" \
    --server="http://127.0.0.1:$CONSENSUS_BEACON_API_PORT" \
    --validatorsDbDir="$CONSENSUS_NODE_DIR/validatorsdb" \
    --logFile="$CONSENSUS_NODE_DIR/validatordb/validator.log" \
    --logLevelFile="$LSTAR_DEBUG_LEVEL" \
    --logRotate \
    --logMaxFiles=5 \
    --graffiti="$CONSENSUS_GRAFFITI"
