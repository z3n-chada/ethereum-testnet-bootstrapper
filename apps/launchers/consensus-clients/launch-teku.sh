#!/bin/bash

#check if we have the neccessary envs to start the script.
env_vars=("PRESET_BASE" "START_FORK_NAME" "END_FORK_NAME" "TEKU_DEBUG_LEVEL" "TESTNET_DIR" "NODE_DIR" "HTTP_WEB3_IP_ADDR" "EXECUTION_HTTP_PORT" "IP_ADDR" "CONSENSUS_P2P_PORT" "BEACON_API_PORT" "BEACON_METRIC_PORT", "CONSENSUS_BOOTNODE_ENR_FILE", "CONSENSUS_CHECKPOINT_FILE", "CONSENSUS_TARGET_PEERS")
for var in "${env_vars[@]}" ; do
    if [[ -z "${!var}" ]]; then
        echo "$var not set"
        exit 1
    fi
done

# lauch the execution client
if [[ -n "$EXECUTION_LAUNCHER" ]]; then
    echo "Teku launching execution client: $EXECUTION_LAUNCHER"
    "$EXECUTION_LAUNCHER" &
fi


while [ ! -f "$CONSENSUS_CHECKPOINT_FILE" ]; do
    sleep 1
done

while [ ! -f "$CONSENSUS_BOOTNODE_ENR_FILE" ]; do
    echo "waiting on bootnode"
    sleep 1
done

bootnode_enr=`cat $CONSENSUS_BOOTNODE_ENR_FILE`

teku \
    --logging="$TEKU_DEBUG_LEVEL" \
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
    --p2p-peer-upper-bound="$CONSENSUS_TARGET_PEERS" \
    --eth1-endpoints="http://$HTTP_WEB3_IP_ADDR:$EXECUTION_HTTP_PORT" \
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
    --validator-keys="$NODE_DIR/keys:$NODE_DIR/secrets" \
    --validators-keystore-locking-enabled=false \
    --ee-endpoint="http://$HTTP_WEB3_IP_ADDR:$EXECUTION_ENGINE_HTTP_PORT" \
    --validators-proposer-default-fee-recipient=0xA18Fd83a55A9BEdB96d66C24b768259eED183be3 \
    --ee-jwt-secret-file="$JWT_SECRET_FILE"
