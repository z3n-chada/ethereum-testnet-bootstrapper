#!/bin/bash
if [[ -n "$EXECUTION_LAUNCHER" ]]; then
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

sleep 50

nimbus_beacon_node \
    --non-interactive \
    --data-dir="$NODE_DIR" \
    --log-file="$NODE_DIR/beacon-log.txt" \
    --network="$TESTNET_DIR" \
    --secrets-dir="$NODE_DIR/secrets" \
    --validators-dir="$NODE_DIR/keys" \
    --rest \
    --rest-address="0.0.0.0" --rest-port="$BEACON_API_PORT" \
    --listen-address="$IP_ADDR" \
    --tcp-port="$CONSENSUS_P2P_PORT" \
    --udp-port="$CONSENSUS_P2P_PORT" \
    --nat="extip:$IP_ADDR" \
    --discv5=true \
    --subscribe-all-subnets \
    --insecure-netkey-password \
    --netkey-file="$NODE_DIR/netkey-file.txt" \
    --graffiti="nimbus-kilnv2:$IP_ADDR" \
    --in-process-validators=true \
    --doppelganger-detection=true \
    --bootstrap-node="$bootnode_enr" \
    --jwt-secret="$JWT_SECRET_FILE" \
    --web3-url=http://"$HTTP_WEB3_IP_ADDR:$EXECUTION_ENGINE_HTTP_PORT" \
    --terminal-total-difficulty-override="$TERMINAL_TOTAL_DIFFICULTY" \
    --dump \
    --log-level="$NIMBUS_DEBUG_LEVEL"
