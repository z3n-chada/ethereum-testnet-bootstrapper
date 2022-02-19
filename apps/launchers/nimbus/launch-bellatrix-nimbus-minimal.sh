#!/bin/bash

DEBUG_LEVEL=$1 
TESTNET_DIR=$2
NODE_DIR=$3
ETH1_ENDPOINT=$4
IP_ADDR=$5
P2P_PORT=$6
RPC_PORT=$7
REST_PORT=$8
METRIC_PORT=$9
TTD=${10}

while [ ! -f "/data/consensus-clients-ready" ]; do
    sleep 1
done

while [ ! -f "/data/local_testnet/bootnode/enr.dat" ]; do
    echo "waiting on bootnode"
    sleep 1
done

bootnode_enr=`cat $TESTNET_DIR/../bootnode/enr.dat`

# --wallets-dir="$NODE_DIR/keys" \
nimbus_beacon_node \
    --non-interactive \
    --max-peers=7 \
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
    --in-process-validators=false \
    --doppelganger-detection=false \
    --terminal-total-difficulty-override="$TTD" \
    --bootstrap-node="$bootnode_enr" &

sleep 1

nimbus_validator_client \
    --data-dir="$NODE_DIR" \
    --secrets-dir="$NODE_DIR/secrets" \
    --validators-dir="$NODE_DIR/keys" \
    --beacon-node="http://127.0.0.1:$REST_PORT"


