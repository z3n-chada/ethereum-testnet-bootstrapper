#!/bin/bash

env_vars=( "PRESET_BASE", "START_FORK_NAME", "END_FORK_NAME", "LIGHTHOUSE_DEBUG_LEVEL", "TESTNET_DIR", "NODE_DIR", "HTTP_WEB3_IP_ADDR", "IP_ADDR", "CONSENSUS_P2P_PORT", "BEACON_METRIC_PORT", "BEACON_RPC_PORT", "BEACON_API_PORT", "VALIDATOR_METRIC_PORT", "GRAFFITI", "NETRESTRICT_RANGE" , "EXECUTION_HTTP_PORT", "TOTAL_TERMINAL_DIFFICULTY", "CONSENSUS_TARGET_PEERS", "VALIDATOR_RPC_PORT", "CONSENSUS_BOOTNODE_ENR_FILE" "CONSENSUS_CHECKPOINT_FILE")

for var in "${env_vars[@]}" ; do
    if [[ -z "$var" ]]; then
        echo "$var not set"
        exit 1
    fi
done

# launch the local exectuion client
if [[ -n "$EXECUTION_LAUNCHER" ]]; then
    echo "lightouse-$IP_ADDR lauching a local execution client"
    "$EXECUTION_LAUNCHER" &
fi

ADDITIONAL_BEACON_ARGS="--logfile=$NODE_DIR/beacon.log --logfile-debug-level=$LIGHTHOUSE_DEBUG_LEVEL"
ADDITIONAL_VALIDATOR_ARGS="--logfile=$NODE_DIR/validator.log --logfile-debug-level=$LIGHTHOUSE_DEBUG_LEVEL"


while [ ! -f "$CONSENSUS_CHECKPOINT_FILE" ]; do
    sleep 1
done

while [ ! -f "$CONSENSUS_BOOTNODE_ENR_FILE" ]; do
    echo "waiting on bootnode"
    sleep 1
done


#if [[ $END_FORK_NAME == "bellatrix" ]]; then
#    ADDITIONAL_BEACON_ARGS="$ADDITIONAL_BEACON_ARGS --merge --terminal-total-difficulty-override=$TERMINAL_TOTAL_DIFFICULTY" 
#    ADDITIONAL_VALIDATOR_ARGS="$ADDITIONAL_VALIDATOR_ARGS --suggested-fee-recipient=0x00000000219ab540356cbb839cbe05303d7705fa"
#    if [ -n "$JWT_SECRET_FILE" ]; then
#        ADDITIONAL_BEACON_ARGS="$ADDITIONAL_BEACON_ARGS --jwt-secrets=$JWT_SECRET_FILE"
#        ADDITIONAL_BEACON_ARGS="$ADDITIONAL_BEACON_ARGS --execution-endpoints=http://$HTTP_WEB3_IP_ADDR:$EXECUTION_ENGINE_AUTH_PORT"
#    else
#        ADDITIONAL_BEACON_ARGS="$ADDITIONAL_BEACON_ARGS --execution-endpoints=http://$HTTP_WEB3_IP_ADDR:$EXECUTION_ENGINE_PORT" 
#    fi
#fi
if [ -n "$JWT_SECRET_FILE" ]; then
    echo "Lightouse using jwt-secret"
        ADDITIONAL_BEACON_ARGS="$ADDITIONAL_BEACON_ARGS --jwt-secrets=$JWT_SECRET_FILE"

    # two cases, either seperate auth ports or one.
    if [ -n "$EXECUTION_AUTH_PORT" ]; then
        # we have same http/ws auth port.
        ADDITIONAL_BEACON_ARGS="$ADDITIONAL_BEACON_ARGS --execution-endpoints=http://$HTTP_WEB3_IP_ADDR:$EXECUTION_AUTH_PORT"
    else
        # lets prefer http for now/ ws doesn't work for at least besu
        if [ -n "$EXECUTION_AUTH_HTTP_PORT" ]; then
            ADDITIONAL_BEACON_ARGS="$ADDITIONAL_BEACON_ARGS --execution-endpoints=http://$HTTP_WEB3_IP_ADDR:$EXECUTION_AUTH_HTTP_PORT"
        else
            ADDITIONAL_BEACON_ARGS="$ADDITIONAL_BEACON_ARGS --execution-endpoints=ws://$WS_WEB3_IP_ADDR:$EXECUTION_AUTH_WS_PORT"
        fi
    fi

else
    echo "Lightouse is not using jwt-secret"
    # no auth.
    if [ -n "$EXECUTION_ENGINE_PORT" ]; then
        # we have same http/ws auth port.
        ADDITIONAL_BEACON_ARGS="$ADDITIONAL_BEACON_ARGS --execution-endpoints=http://$HTTP_WEB3_IP_ADDR:$EXECUTION_ENGINE_PORT"
    else
        # lets prefer ws for now.
        if [ -n "$EXECUTION_ENGINE_HTTP_PORT" ]; then
            ADDITIONAL_BEACON_ARGS="$ADDITIONAL_BEACON_ARGS --execution-endpoints=http://$HTTP_WEB3_IP_ADDR:$EXECUTION_ENGINE_HTTP_PORT"
        else
            ADDITIONAL_BEACON_ARGS="$ADDITIONAL_BEACON_ARGS --execution-endpoints=ws://$WS_WEB3_IP_ADDR:$EXECUTION_ENGINE_WS_PORT"
        fi
    fi

fi
ADDITIONAL_BEACON_ARGS="$ADDITIONAL_BEACON_ARGS --merge --terminal-total-difficulty-override=$TERMINAL_TOTAL_DIFFICULTY" 

ADDITIONAL_VALIDATOR_ARGS="$ADDITIONAL_VALIDATOR_ARGS --suggested-fee-recipient=0x00000000219ab540356cbb839cbe05303d7705fa"


if [ ! -f "$TESTNET_DIR/boot_enr.yaml" ]; then
    bootnode_enr=`cat $CONSENSUS_BOOTNODE_ENR_FILE`
    echo "- $bootnode_enr" > $TESTNET_DIR/boot_enr.yaml
fi


# lastly see if we are running a tx-fuzz instance.

lighthouse \
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
