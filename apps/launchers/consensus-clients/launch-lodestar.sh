#!/bin/bash

env_vars=( "PRESET_BASE", "START_FORK_NAME", "END_FORK_NAME", "LODESTAR_DEBUG_LEVEL", "TESTNET_DIR", "NODE_DIR", "HTTP_WEB3_IP_ADDR", "IP_ADDR", "CONSENSUS_P2P_PORT", "BEACON_METRIC_PORT", "BEACON_RPC_PORT", "BEACON_API_PORT", "VALIDATOR_METRIC_PORT", "GRAFFITI", "NETRESTRICT_RANGE" , "EXECUTION_HTTP_PORT", "TOTALTERMINALDIFFICULTY", "CONSENSUS_TARGET_PEERS", "VALIDATOR_RPC_PORT", "CONSENSUS_BOOTNODE_ENR_FILE", "CONSENSUS_CHECKPOINT_FILE")

for var in "${env_vars[@]}" ; do
    if [[ -z "$var" ]]; then
        echo "$var not set"
        exit 1
    fi
done

ADDITIONAL_BEACON_ARGS="--logFile=$NODE_DIR/beacon.log"

while [ ! -f "$CONSENSUS_CHECKPOINT_FILE" ]; do
    sleep 1
done

while [ ! -f "$CONSENSUS_BOOTNODE_ENR_FILE" ]; do
    echo "waiting on bootnode"
    sleep 1
done

bootnode_enr=`cat $CONSENSUS_BOOTNODE_ENR_FILE`

# launch the local exectuion client
if [[ -n "$EXECUTION_LAUNCHER" ]]; then
    echo "lodestar-$IP_ADDR lauching a local execution client"
    "$EXECUTION_LAUNCHER" &
fi

if [[ $END_FORK_NAME == "bellatrix" ]]; then
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --execution.urls=http://$HTTP_WEB3_IP_ADDR:$EXECUTION_ENGINE_PORT --terminal-total-difficulty-override=$TERMINAL_TOTAL_DIFFICULTY" 
    ADDITIONAL_VALIDATOR_ARGS="--terminal-total-difficulty-override=$TERMINAL_TOTAL_DIFFICULTY"
fi

sleep 10

    #--logLevelFile="$LODESTAR_DEBUG_LEVEL" \
    #--paramsFile="$TESTNET_DIR/config.yaml" \
    #--logLevel="$LODESTAR_DEBUG_LEVEL" \
    #--logLevelFile=debug \
lodestar beacon \
    --rootDir="$NODE_DIR" \
    --configFile="$TESTNET_DIR/config.yaml" \
    --paramsFile="$TESTNET_DIR/config.yaml" \
    --genesisStateFile="$TESTNET_DIR/genesis.ssz" \
    --network.discv5.bootEnrs="$bootnode_enr" \
    --network.connectToDiscv5Bootnodes \
    --network.discv5.enabled=true \
    --network.subscribeAllSubnets \
    --eth1.enabled=true \
    --api.rest.port="$BEACON_API_PORT" \
    --eth1.providerUrls="http://$HTTP_WEB3_IP_ADDR:$EXECUTION_HTTP_PORT" \
    --execution.urls="http://$HTTP_WEB3_IP_ADDR:$EXECUTION_ENGINE_PORT" \
    --api.rest.enabled=true \
    --api.rest.host=0.0.0.0 \
    --api.rest.api="*" \
    --logFile="$NODE_DIR/beacon.log" \
    --logRotate \
    --logMaxFiles=5 \
    --enr.ip="$IP_ADDR" \
    --metrics.enabled \
    --metrics.serverPort="$BEACON_METRIC_PORT" \
    --terminal-total-difficulty-override="$TERMINAL_TOTAL_DIFFICULTY" \
    --eth1.depositContractDeployBlock=0 &
#     --rootDir="$NODE_DIR" \
#     --configFile="$TESTNET_DIR/config.yaml" \
#     --paramsFile="$TESTNET_DIR/config.yaml" \
#     --genesisStateFile="$TESTNET_DIR/genesis.ssz" \
#     --network.discv5.bootEnrs="$bootnode_enr" \
#     --network.connectToDiscv5Bootnodes \
#     --network.discv5.enabled=true \
#     --network.subscribeAllSubnets \
#     --eth1.enabled=true \
#     --api.rest.port="$BEACON_API_PORT" \
#     --eth1.providerUrls="http://$HTTP_WEB3_IP_ADDR:$EXECUTION_HTTP_PORT" \
#     --api.rest.enabled=true \
#     --api.rest.host=0.0.0.0 \
#     --api.rest.api="*" \
#     --logLevel=debug \
#     --logRotate \
#     --logMaxFiles=5 \
#     --enr.ip="$IP_ADDR" \
#     --metrics.enabled \
#     --metrics.serverPort="$BEACON_METRIC_PORT" $ADDITIONAL_BEACON_ARGS \
#     --eth1.depositContractDeployBlock=0 &

sleep 10

lodestar validator \
    --rootDir="$NODE_DIR" \
    --paramsFile="$TESTNET_DIR/config.yaml" \
    --keystoresDir="$NODE_DIR/keys/" \
    --secretsDir="$NODE_DIR/secrets/" \
    --server="http://127.0.0.1:$BEACON_API_PORT" \
    --validatorsDbDir="$NODE_DIR/validatorsdb" \
    --logFile="$NODE_DIR/validatordb/validator.log" \
    --logLevelFile="$LODESTAR_DEBUG_LEVEL" \
    --logRotate \
    --logMaxFiles=5 \
    --terminal-total-difficulty-override="$TERMINAL_TOTAL_DIFFICULTY" \
    --graffiti="$GRAFFITI"


    # --rootDir="$NODE_DIR" \
    # --paramsFile="$TESTNET_DIR/config.yaml" \
    # --keystoresDir="$NODE_DIR/keys/" \
    # --secretsDir="$NODE_DIR/secrets/" \
    # --server="http://127.0.0.1:$BEACON_API_PORT" \
    # --validatorsDbDir="$NODE_DIR/validatorsdb" \
    # --logLevelFile="$LODESTAR_DEBUG_LEVEL" \
    # --logRotate \
    # --logMaxFiles=5  $ADDITIONAL_VALIDATOR_ARGS \
    # --graffiti="$GRAFFITI" 
