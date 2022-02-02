#!/bin/bash


DEBUG_LEVEL=$1 
TESTNET_DIR=$2
NODE_DIR=$3
ETH1_ENDPOINT=$4
IP_ADDR=$5
P2P_PORT=$6
REST_PORT=$7
HTTP_PORT=$8
METRICS_PORT=$9
TTD_OVERRIDE=${10}
TARGET_PEERS=${11}

while [ ! -f "/data/consensus-clients-ready" ]; do
    sleep 1
done

while [ ! -f "/data/local_testnet/bootnode/enr.dat" ]; do
    echo "waiting on bootnode"
    sleep 1
done

if [ ! -f "$TESTNET_DIR/boot_enr.yaml" ]; then
    bootnode_enr=`cat /data/local_testnet/bootnode/enr.dat`
    echo "- $bootnode_enr" > $TESTNET_DIR/boot_enr.yaml
fi

lighthouse \
	--datadir $NODE_DIR \
	--debug-level $DEBUG_LEVEL \
	bn \
    --target-peers $TARGET_PEERS \
	--testnet-dir $TESTNET_DIR \
	--staking \
    --metrics --metrics-address=0.0.0.0 --metrics-port="$METRICS_PORT" \
    --http-allow-sync-stalled \
	--enr-address "$IP_ADDR" \
	--enr-udp-port $P2P_PORT \
	--enr-tcp-port $P2P_PORT \
	--port $P2P_PORT \
	--http --http-port $REST_PORT \
	--http-address 0.0.0.0 \
	--http-allow-origin "*" \
	--eth1 --eth1-endpoints "$ETH1_ENDPOINT" \
    --merge \
    --disable-packet-filter \
    --execution-endpoints="$ETH1_ENDPOINT" \
    --terminal-total-difficulty-override=$TTD_OVERRIDE &

sleep 10
lighthouse \
	--datadir $NODE_DIR \
	--debug-level $DEBUG_LEVEL \
	vc \
	--testnet-dir $TESTNET_DIR \
    --validators-dir "$NODE_DIR/keys" \
    --secrets-dir "$NODE_DIR/secrets" \
	--init-slashing-protection \
	--beacon-nodes "http://localhost:$REST_PORT"
