#!/bin/bash

# launch the local exectuion client
if [[ -n "$EXECUTION_LAUNCHER" ]]; then
    echo "lightouse-$IP_ADDR lauching a local execution client"
    "$EXECUTION_LAUNCHER" &
fi

while [ ! -f "$CONSENSUS_CHECKPOINT_FILE" ]; do
    sleep 1
done

while [ ! -f "$CONSENSUS_BOOTNODE_ENR_FILE" ]; do
    echo "waiting on bootnode"
    sleep 1
done


if [ ! -f "$TESTNET_DIR/boot_enr.yaml" ]; then
    bootnode_enr=`cat $CONSENSUS_BOOTNODE_ENR_FILE`
    echo "- $bootnode_enr" > $TESTNET_DIR/boot_enr.yaml
fi

lighthouse \
    --logfile="$NODE_DIR/beacon.log" \
    --logfile-debug-level="$LIGHTHOUSE_DEBUG_LEVEL" \
	--debug-level=$LIGHTHOUSE_DEBUG_LEVEL \
	--datadir=$NODE_DIR \
	--testnet-dir $TESTNET_DIR \
	bn \
    --disable-enr-auto-update \
	--enr-address "$IP_ADDR" \
	--enr-udp-port "$CONSENSUS_P2P_PORT" --enr-tcp-port "$CONSENSUS_P2P_PORT" \
	--port="$CONSENSUS_P2P_PORT" --discovery-port "$CONSENSUS_P2P_PORT" \
    --eth1 \
	--http \
	--http-address=0.0.0.0 \
	--http-port="$BEACON_API_PORT" \
    --http-allow-origin="*" \
    --metrics \
    --metrics-address=0.0.0.0 \
    --metrics-port="$BEACON_METRIC_PORT" \
    --metrics-allow-origin="*" \
    --listen-address=0.0.0.0 \
    --graffiti="$GRAFFITI" \
    --target-peers="$CONSENSUS_TARGET_PEERS" \
    --http-allow-sync-stalled \
    --disable-packet-filter \
    --eth1-endpoints="http://$HTTP_WEB3_IP_ADDR:$EXECUTION_HTTP_PORT" \
    --validator-monitor-auto \
    --enable-private-discovery $ADDITIONAL_BEACON_ARGS \
    --execution-endpoints="http://$HTTP_WEB3_IP_ADDR:$EXECUTION_ENGINE_HTTP_PORT" \
    --merge \
    --terminal-total-difficulty-override="$TERMINAL_TOTAL_DIFFICULTY" \
    --jwt-secrets="$JWT_SECRET_FILE" \
    --subscribe-all-subnets &

sleep 10
lighthouse \
    --testnet-dir="$TESTNET_DIR" \
	vc \
    --validators-dir "$NODE_DIR/keys" \
    --secrets-dir "$NODE_DIR/secrets" \
	--init-slashing-protection \
    --server="http://127.0.0.1:$BEACON_API_PORT" \
    --graffiti="$GRAFFITI" \
    --http --http-port="$VALIDATOR_RPC_PORT" $ADDITIONAL_VALIDATOR_ARGS \
    --metrics --metrics-address=0.0.0.0 --metrics-port="$VALIDATOR_METRIC_PORT" \
    --suggested-fee-recipient=0x00000000219ab540356cbb839cbe05303d7705fa \
    --logfile="$NODE_DIR/validator.log" --logfile-debug-level="$LIGHTHOUSE_DEBUG_LEVEL"
