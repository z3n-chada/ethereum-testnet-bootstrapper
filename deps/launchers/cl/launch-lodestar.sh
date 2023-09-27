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

#TODO prometheus
BEACON_NODE_CMD="lodestar"
BEACON_NODE_CMD+=" beacon"
BEACON_NODE_CMD+=" --bootnodes=$bootnode_enr"
BEACON_NODE_CMD+=" --logLevel=$CONSENSUS_LOG_LEVEL"
BEACON_NODE_CMD+=" --port=$CONSENSUS_P2P_PORT"
BEACON_NODE_CMD+=" --discoveryPort=$CONSENSUS_P2P_PORT"
BEACON_NODE_CMD+=" --dataDir=$CONSENSUS_NODE_DIR"
BEACON_NODE_CMD+=" --paramsFile=$CONSENSUS_CONFIG_FILE"
BEACON_NODE_CMD+=" --genesisStateFile=$CONSENSUS_GENESIS_FILE"
BEACON_NODE_CMD+=" --eth1.depositContractDeployBlock=0"
BEACON_NODE_CMD+=" --network.connectToDiscv5Bootnodes=true"
BEACON_NODE_CMD+=" --discv5=true"
BEACON_NODE_CMD+=" --execution.urls=http://127.0.0.1:$CL_EXECUTION_ENGINE_HTTP_PORT"
BEACON_NODE_CMD+=" --rest=true"
BEACON_NODE_CMD+=" --rest.address=0.0.0.0"
BEACON_NODE_CMD+=" --rest.namespace=*"
BEACON_NODE_CMD+=" --rest.port=$CONSENSUS_BEACON_API_PORT"
BEACON_NODE_CMD+=" --nat=true"
BEACON_NODE_CMD+=" --enr.ip=$IP_ADDRESS"
BEACON_NODE_CMD+=" --enr.tcp=$CONSENSUS_P2P_PORT"
BEACON_NODE_CMD+=" --enr.udp=$CONSENSUS_CONSENSUS_P2P_PORT"
BEACON_NODE_CMD+=" --subscribeAllSubnets=true"
BEACON_NODE_CMD+=" --jwt-secret=$JWT_SECRET_FILE"
BEACON_NODE_CMD+=" --metrics=true"
BEACON_NODE_CMD+=" --metrics.address=0.0.0.0"
BEACON_NODE_CMD+=" --metrics.port=$CONSENSUS_BEACON_METRIC_PORT"

VALIDATOR_CMD="lodestar"
VALIDATOR_CMD+=" validator"
VALIDATOR_CMD+=" --logLevel=$CONSENSUS_LOG_LEVEL"
VALIDATOR_CMD+=" --dataDir=$CONSENSUS_NODE_DIR"
VALIDATOR_CMD+=" --paramsFile=$CONSENSUS_CONFIG_FILE"
VALIDATOR_CMD+=" --beaconNodes=http://127.0.0.1:$CONSENSUS_BEACON_API_PORT"
VALIDATOR_CMD+=" --keystoresDir=$CONSENSUS_NODE_DIR/keys/"
VALIDATOR_CMD+=" --secretsDir=$CONSENSUS_NODE_DIR/secrets/"
VALIDATOR_CMD+=" --suggestedFeeRecipient=0x00000000219ab540356cbb839cbe05303d7705fa"
VALIDATOR_CMD+=" --metrics"
VALIDATOR_CMD+=" --metrics.address=0.0.0.0"
VALIDATOR_CMD+=" --metrics.port=$CONSENSUS_VALIDATOR_METRIC_PORT"
VALIDATOR_CMD+=" --graffiti=$CONSENSUS_GRAFFITI"

echo "Launching lodestar beacon-node."
eval "$BEACON_NODE_CMD" &

sleep 10

echo "Launching lodestar validator."
eval "$VALIDATOR_CMD"



















#lodestar beacon \
#    --dataDir="$CONSENSUS_NODE_DIR" \
#    --paramsFile="$CONSENSUS_CONFIG_FILE" \
#    --genesisStateFile="$CONSENSUS_GENESIS_FILE" \
#    --execution.urls="http://127.0.0.1:$CL_EXECUTION_ENGINE_HTTP_PORT" \
#    --jwt-secret="$JWT_SECRET_FILE" \
#    --bootnodes="$bootnode_enr" \
#    --network.connectToDiscv5Bootnodes=true \
#    --discv5 \
#    --rest \
#    --rest.address=0.0.0.0 \
#    --rest.port="$CONSENSUS_BEACON_API_PORT" \
#    --rest.namespace="*" \
#    --logLevel="$CONSENSUS_LOG_LEVEL" \
#    --logFile="$CONSENSUS_NODE_DIR/beacon.log" \
#    --port="$CONSENSUS_P2P_PORT" \
#    --discoveryPort="$CONSENSUS_CONSENSUS_P2P_PORT" \
#    --enr.ip="$IP_ADDRESS" \
#    --enr.tcp="$CONSENSUS_P2P_PORT" \
#    --enr.udp="$CONSENSUS_CONSENSUS_P2P_PORT" \
#    --subscribeAllSubnets=true \
#    --eth1.depositContractDeployBlock=0 \
#    --suggestedFeeRecipient=0x00000000219ab540356cbb839cbe05303d7705fa &
#
#sleep 10
#
#lodestar validator \
#    --dataDir="$CONSENSUS_NODE_DIR" \
#    --paramsFile="$CONSENSUS_CONFIG_FILE" \
#    --keystoresDir="$CONSENSUS_NODE_DIR/keys/" \
#    --secretsDir="$CONSENSUS_NODE_DIR/secrets/" \
#    --beaconNodes="http://127.0.0.1:$CONSENSUS_BEACON_API_PORT" \
#    --validatorsDbDir="$CONSENSUS_NODE_DIR/validatorsdb" \
#    --logFile="$CONSENSUS_NODE_DIR/validatordb/validator.log" \
#    --logLevel="$CONSENSUS_LOG_LEVEL" \
#    --graffiti="$CONSENSUS_GRAFFITI" \
#    --force
