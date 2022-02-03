#!/bin/bash

DEBUG_LEVEL=$1 
TESTNET_DIR=$2
NODE_DIR=$3
ETH1_ENDPOINT=$4
IP_ADDR=$5
P2P_PORT=$6
REST_PORT=$7
HTTP_PORT=$8

sleep 5 # give bootstrapper enough time to remove the checkpoint file.

while [ ! -f "/data/consensus-clients-ready" ]; do
    sleep 1
done

while [ ! -f "/data/local_testnet/bootnode/enr.dat" ]; do
    echo "waiting on bootnode"
    sleep 1
done

bootnode_enr=`cat $TESTNET_DIR/../bootnode/enr.dat`

teku \
    --initial-state "$TESTNET_DIR/genesis.ssz" \
    --network "$TESTNET_DIR/config.yaml" \
    --data-path "$NODE_DIR" \
    --data-storage-mode=PRUNE \
    --p2p-enabled=true \
    --p2p-discovery-enabled=true \
    --p2p-advertised-ip="$IP_ADDR" \
    --p2p-peer-lower-bound=1 \
    --p2p-port="$P2P_PORT" \
    --p2p-advertised-port="$P2P_PORT" \
    --p2p-advertised-udp-port="$P2P_PORT" \
    --logging="$DEBUG_LEVEL" \
    --p2p-peer-upper-bound=8 \
    --eth1-endpoint "$ETH1_ENDPOINT" \
    --p2p-discovery-bootnodes="$bootnode_enr" \
    --metrics-enabled=true \
    --metrics-interface=0.0.0.0 \
    --metrics-port="$HTTP_PORT" \
    --rest-api-enabled=true \
    --rest-api-docs-enabled=true \
    --rest-api-interface=0.0.0.0 \
    --rest-api-port="$REST_PORT" \
    --metrics-host-allowlist="*" \
    --rest-api-host-allowlist="*" \
    --data-storage-non-canonical-blocks-enabled=true \
    --validators-graffiti="teku-$IP_ADDR" \
    --validator-keys "$NODE_DIR/keys:$NODE_DIR/secrets" \
    --validators-keystore-locking-enabled=false 
