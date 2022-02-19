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
METRICS_PORT=${12}
TTD_OVERRIDE=${13}
TARGET_PEERS=${14}

ADDITIONAL_ARGS=""

while [ ! -f "/data/consensus-clients-ready" ]; do
    sleep 1
done

while [ ! -f "/data/local_testnet/bootnode/enr.dat" ]; do
    echo "waiting on bootnode"
    sleep 1
done

bootnode_enr=`cat $TESTNET_DIR/../bootnode/enr.dat`

if [ ! -f "$TESTNET_DIR/boot_enr.yaml" ]; then
    bootnode_enr=`cat /data/local_testnet/bootnode/enr.dat`
    echo "- $bootnode_enr" > $TESTNET_DIR/boot_enr.yaml
fi

if [[ $END_FORK == "bellatrix" ]]; then
    ADDITIONAL_ARGS="--merge --terminal-total-difficulty-override=$TTD_OVERRIDE"
else
    ADDITIONAL_ARGS="--staking"
fi

lighthouse \
	--datadir $NODE_DIR \
	--debug-level $DEBUG_LEVEL \
	bn \
    --target-peers "$TARGET_PEERS" \
	--testnet-dir $TESTNET_DIR \
    --boot-nodes "$bootnode_enr" \
    --http-allow-sync-stalled \
	--enr-address "$IP_ADDR" \
	--enr-udp-port "$P2P_PORT" \
	--enr-tcp-port "$P2P_PORT" \
    --discovery-port "$P2P_PORT" \
	--port $P2P_PORT \
	--http --http-port $REST_PORT \
	--http-address 0.0.0.0 \
	--http-allow-origin "*" \
	--eth1 --eth1-endpoints "$ETH1_ENDPOINT" \
    --disable-packet-filter $ADDITIONAL_ARGS \
    --subscribe-all-subnets &

sleep 10
lighthouse \
	--datadir $NODE_DIR \
	--debug-level $DEBUG_LEVEL \
	vc \
    --beacon-nodes "http://localhost:$REST_PORT" \
	--testnet-dir $TESTNET_DIR \
    --validators-dir "$NODE_DIR/keys" \
    --secrets-dir "$NODE_DIR/secrets" \
	--init-slashing-protection \
