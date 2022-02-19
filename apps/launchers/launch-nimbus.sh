#!/bin/bash
PRESET_BASE=$1
STARK_FORK=$2
END_FORK=$3
DEBUG_LEVEL=$4
TESTNET_DIR=$5
NODE_DIR=$6
ETH1_ENDPOINT=$7
IP_ADDR=$8
P2P_PORT=$9
RPC_PORT=${10}
REST_PORT=${11}
METRIC_PORT=${12}
TTD_OVERRIDE=${13}
TARGET_PEERS=${14}

while [ ! -f "/data/consensus-clients-ready" ]; do
    sleep 1
done

while [ ! -f "/data/local_testnet/bootnode/enr.dat" ]; do
    echo "waiting on bootnode"
    sleep 1
done

bootnode_enr=`cat $TESTNET_DIR/../bootnode/enr.dat`

if [[ $END_FORK == "bellatrix" ]]; then
    ADDITIONAL_ARGS="--terminal-total-difficulty-override=$TTD_OVERRIDE"
fi 

nimbus_beacon_node \
    --non-interactive \
    --max-peers="$TARGET_PEERS" \
    --data-dir="$NODE_DIR" \
    --network="$TESTNET_DIR" \
    --secrets-dir="$NODE_DIR/secrets" \
    --validators-dir="$NODE_DIR/keys" \
    --rpc \
    --rpc-address="0.0.0.0" --rpc-port="$RPC_PORT" \
    --rest \
    --rest-address="0.0.0.0" --rest-port="$REST_PORT" \
    --log-level="$DEBUG_LEVEL" \
    --listen-address="$IP_ADDR" \
    --tcp-port="$P2P_PORT" \
    --udp-port="$P2P_PORT" \
    --nat="extip:$IP_ADDR" \
    --discv5=true \
    --subscribe-all-subnets \
    --web3-url="$ETH1_ENDPOINT" \
    --insecure-netkey-password \
    --netkey-file="$NODE_DIR/netkey-file.txt" \
    --in-process-validators=true \
    --doppelganger-detection=false $ADDITIONAL_ARGS\
    --bootstrap-node="$bootnode_enr" 

