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
REST_PORT=${10}
HTTP_PORT=${11}

ADDITIONAL_ARGS=""

while [ ! -f "/data/consensus-clients-ready" ]; do
    sleep 1
done

while [ ! -f "/data/local_testnet/bootnode/enr.dat" ]; do
    echo "waiting on bootnode"
    sleep 1
done

bootnode_enr=`cat $TESTNET_DIR/../bootnode/enr.dat`

if [[ $END_FORK == "bellatrix" ]]; then
    ADDITIONAL_ARGS="--Xee-endpoint=$ETH1_ENDPOINT --Xvalidators-proposer-default-fee-recipient=0xA18Fd83a55A9BEdB96d66C24b768259eED183be3 "
else
    ADDITIONAL_ARGS=""
fi

teku \
    --initial-state="$TESTNET_DIR/genesis.ssz" \
    --logging="$DEBUG_LEVEL" \
    --network="$TESTNET_DIR/config.yaml" \
    --data-path="$NODE_DIR" \
    --data-storage-mode=PRUNE \
    --p2p-enabled=true \
    --p2p-discovery-enabled=true \
    --p2p-advertised-ip="$IP_ADDR" \
    --p2p-peer-lower-bound=1 \
    --p2p-port="$P2P_PORT" \
    --p2p-advertised-port="$P2P_PORT" \
    --p2p-advertised-udp-port="$P2P_PORT" \
    --p2p-peer-upper-bound=8 \
    --eth1-endpoint="$ETH1_ENDPOINT" \
    --p2p-discovery-bootnodes="$bootnode_enr" \
    --p2p-subscribe-all-subnets-enabled=true \
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
    --Xee-version=kiln \
    --validator-keys="$NODE_DIR/keys:$NODE_DIR/secrets" $ADDITIONAL_ARGS \
    --validators-keystore-locking-enabled=false 
