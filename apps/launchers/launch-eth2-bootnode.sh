#!/bin/bash

IP_ADDRESS=$1
ENR_UDP=$2
API_PORT=$3
PRIV_KEY=$4
ENR_PATH=$5

if [ ! -f "/data/testnet-ready" ]; then
    sleep 10
    # TODO: fix this.
fi 

mkdir -p /data/local_testnet/bootnode/

"/source/apps/launchers/eth2-bootnode-delay-fetch-and-write-enr.sh" "$IP_ADDRESS:$API_PORT/enr" $5 &

eth2-bootnode \
    --priv "$PRIV_KEY" \
    --enr-ip $IP_ADDRESS \
    --enr-udp $ENR_UDP \
    --listen-ip 0.0.0.0 \
    --listen-udp $ENR_UDP \
    --api-addr "0.0.0.0:$API_PORT"
