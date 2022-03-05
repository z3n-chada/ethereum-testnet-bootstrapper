#!/bin/bash

env_vars=( "PRESET_BASE", "START_FORK", "END_FORK", "DEBUG_LEVEL", "TESTNET_DIR", "NODE_DIR", "HTTP_WEB3_IP_ADDR", "IP_ADDR", "CONSENSUS_P2P_PORT", "BEACON_METRIC_PORT", "BEACON_RPC_PORT", "BEACON_API_PORT", "VALIDATOR_METRIC_PORT", "GRAFFITI", "NETRESTRICT_RANGE" , "EXECUTION_HTTP_PORT", "TERMINALTOTALDIFFICULTY")

for var in "${env_vars[@]}" ; do
    if [[ -z "$var" ]]; then
        echo "$var not set"
        exit 1
    fi
done

while [ ! -f "/data/consensus-clients-ready" ]; do
    sleep 1
done

while [ ! -f "/data/local_testnet/bootnode/enr.dat" ]; do
    echo "waiting on bootnode"
    sleep 1
done

bootnode_enr=`cat /data/local_testnet/bootnode/enr.dat `

if [[ $END_FORK == "bellatrix" ]]; then
    ADDITIONAL_ARGS="--terminal-total-difficulty-override=$TERMINALTOTALDIFFICULTY"
fi 

if [[ -n "$EXECUTION_LAUNCHER" ]]; then
    "$EXECUTION_LAUNCHER" &
fi

sleep 30

nimbus_beacon_node \
    --non-interactive \
    --data-dir="$NODE_DIR" \
    --network="$TESTNET_DIR" \
    --secrets-dir="$NODE_DIR/secrets" \
    --validators-dir="$NODE_DIR/keys" \
    --rpc \
    --rpc-address="0.0.0.0" --rpc-port="$BEACON_RPC_PORT" \
    --rest \
    --rest-address="0.0.0.0" --rest-port="$BEACON_API_PORT" \
    --log-level="$DEBUG_LEVEL" \
    --listen-address="$IP_ADDR" \
    --tcp-port="$CONSENSUS_P2P_PORT" \
    --udp-port="$CONSENSUS_P2P_PORT" \
    --nat="extip:$IP_ADDR" \
    --discv5=true \
    --subscribe-all-subnets \
    --web3-url="http://$HTTP_WEB3_IP_ADDR:$EXECUTION_HTTP_PORT" \
    --insecure-netkey-password \
    --netkey-file="$NODE_DIR/netkey-file.txt" \
    --in-process-validators=true \
    --doppelganger-detection=false $ADDITIONAL_ARGS\
    --bootstrap-node="$bootnode_enr" 

