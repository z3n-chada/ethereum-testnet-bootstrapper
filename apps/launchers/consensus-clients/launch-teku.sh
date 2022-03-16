#!/bin/bash

#check if we have the neccessary envs to start the script.
env_vars=("PRESET_BASE" "START_FORK" "END_FORK" "DEBUG_LEVEL" "TESTNET_DIR" "NODE_DIR" "HTTP_WEB3_IP_ADDR" "EXECUTION_HTTP_PORT" "IP_ADDR" "CONSENSUS_P2P_PORT" "BEACON_API_PORT" "BEACON_METRIC_PORT")
for var in "${env_vars[@]}" ; do
    if [[ -z "$var" ]]; then
        echo "$var not set"
        exit 1
    fi
done


ADDITIONAL_ARGS=""

# lauch the execution client

while [ ! -f "/data/consensus-clients-ready" ]; do
    sleep 1
done

while [ ! -f "/data/local_testnet/bootnode/enr.dat" ]; do
    echo "waiting on bootnode"
    sleep 1
done

bootnode_enr=`cat $TESTNET_DIR/../bootnode/enr.dat`

if [[ $END_FORK == "bellatrix" ]]; then
    # if [[ -z "$XEE_VERSION" ]]; then
    #     echo "Failed to load the engine version, specify with consensus-additional-env: xee-version: {kintsugi/kiln/kilnv2}"
    #     exit 1
    # fi
    ADDITIONAL_ARGS="--ee-endpoint="http://$HTTP_WEB3_IP_ADDR:$EXECUTION_HTTP_PORT" --validators-proposer-default-fee-recipient=0xA18Fd83a55A9BEdB96d66C24b768259eED183be3 "
else
    ADDITIONAL_ARGS=""
fi

if [[ -n "$EXECUTION_LAUNCHER" ]]; then
    echo "Teku launching execution client"
    ls "/data/"
    ls "/data/local_testnet/execution-bootstrapper/"
    "$EXECUTION_LAUNCHER" &
fi

teku \
    --network="$TESTNET_DIR/config.yaml" \
    --initial-state="$TESTNET_DIR/genesis.ssz" \
    --data-path="$NODE_DIR" \
    --data-storage-mode=PRUNE \
    --p2p-enabled=true \
    --p2p-advertised-ip="$IP_ADDR" \
    --p2p-advertised-port="$CONSENSUS_P2P_PORT" \
    --p2p-advertised-udp-port="$CONSENSUS_P2P_PORT" \
    --p2p-discovery-enabled=true \
    --p2p-peer-lower-bound=1 \
    --p2p-port="$CONSENSUS_P2P_PORT" \
    --logging="$DEBUG_LEVEL" \
    --p2p-peer-upper-bound=8 \
    --eth1-endpoint="http://$HTTP_WEB3_IP_ADDR:$EXECUTION_HTTP_PORT" \
    --p2p-discovery-bootnodes="$bootnode_enr" \
    --p2p-subscribe-all-subnets-enabled=true \
    --metrics-enabled=true \
    --metrics-interface=0.0.0.0 \
    --metrics-port="$BEACON_METRIC_PORT" \
    --rest-api-enabled=true \
    --rest-api-docs-enabled=true \
    --rest-api-interface=0.0.0.0 \
    --rest-api-port="$BEACON_API_PORT" \
    --metrics-host-allowlist="*" \
    --rest-api-host-allowlist="*" \
    --data-storage-non-canonical-blocks-enabled=true \
    --validators-graffiti="teku-$IP_ADDR" \
    --validator-keys="$NODE_DIR/keys:$NODE_DIR/secrets" $ADDITIONAL_ARGS \
    --validators-keystore-locking-enabled=false 
