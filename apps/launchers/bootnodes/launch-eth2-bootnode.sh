#!/bin/bash

env_vars=("IP_ADDR" "CONSENSUS_BOOTNODE_API_PORT" "CONSENSUS_BOOTNODE_PRIVATE_KEY" "CONSENSUS_BOOTNODE_START_IP_ADDR" "CONSENSUS_BOOTNODE_ENR_FILE" "CONSENSUS_BOOTNODE_ENR_PORT")

for var in "${env_vars[@]}" ; do
    if [[ -z "$var" ]]; then
        echo "$var not set"
        exit 1
    fi
done

# some more exotic setups don't run with the /data/local_testnet/ already mounted in.
# we support this by waiting for it to be done.
while [ ! -d "/data/local_testnet" ]; do
    ls /data/
    echo "waiting for local_testnet data to be mapped in."
    sleep 1
done

mkdir -p /data/local_testnet/bootnode/

"/source/apps/launchers/eth2-bootnode-delay-fetch-and-write-enr.sh" "$CONSENSUS_BOOTNODE_START_IP_ADDR:$CONSENSUS_BOOTNODE_API_PORT/enr" "$CONSENSUS_BOOTNODE_ENR_FILE" &

eth2-bootnode \
    --priv "$CONSENSUS_BOOTNODE_PRIVATE_KEY" \
    --enr-ip "$CONSENSUS_BOOTNODE_START_IP_ADDR" \
    --enr-udp "$CONSENSUS_BOOTNODE_ENR_PORT" \
    --listen-ip 0.0.0.0 \
    --listen-udp "$CONSENSUS_BOOTNODE_ENR_PORT" \
    --api-addr "0.0.0.0:$CONSENSUS_BOOTNODE_API_PORT"
