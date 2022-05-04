#!/bin/bash 
env_vars=( "PRESET_BASE", "START_FORK_NAME", "END_FORK_NAME", "DEBUG_LEVEL", "TESTNET_DIR", "NODE_DIR", "HTTP_WEB3_IP_ADDR", "IP_ADDR", "CONSENSUS_P2P_PORT", "BEACON_METRIC_PORT", "BEACON_RPC_PORT", "BEACON_API_PORT", "VALIDATOR_METRIC_PORT", "GRAFFITI", "NETRESTRICT_RANGE" , "EXECUTION_HTTP_PORT", "CONSENSUS_CHECKPOINT_FILE", "CONSENSUS_BOOTNODE_ENR_FILE", "CONSENSUS_TARGET_PEERS")

for var in "${env_vars[@]}" ; do
    if [[ -z "$var" ]]; then
        echo "$var not set"
        exit 1
    fi
done

if [[ -n "$EXECUTION_LAUNCHER" ]]; then
    "$EXECUTION_LAUNCHER" &
fi

ADDITIONAL_BEACON_ARGS="--log-file=$NODE_DIR/beacon.log" 
ADDITIONAL_VALIDATOR_ARGS="--log-file=$NODE_DIR/validator.log"


while [ ! -f "$CONSENSUS_BOOTNODE_ENR_FILE" ]; do
    echo "waiting on bootnode"
    sleep 1
done

bootnode_enr=`cat $CONSENSUS_BOOTNODE_ENR_FILE`


# TODO allow for more port descriptions easily across clients.

# Test Besu

ADDITIONAL_BEACON_ARGS="$ADDITIONAL_BEACON_ARGS --jwt-secret=$JWT_SECRET_FILE"
# override
if [ -n "$EXECUTION_ENGINE_PORT" ]; then
    # we have same http/ws auth port.
    ADDITIONAL_BEACON_ARGS="$ADDITIONAL_BEACON_ARGS --http-web3provider=http://$HTTP_WEB3_IP_ADDR:$EXECUTION_ENGINE_PORT"
else
    ADDITIONAL_BEACON_ARGS="$ADDITIONAL_BEACON_ARGS --http-web3provider=http://$HTTP_WEB3_IP_ADDR:$EXECUTION_AUTH_HTTP_PORT"
fi

# if [ -n "$JWT_SECRET_FILE" ]; then
#         ADDITIONAL_BEACON_ARGS="$ADDITIONAL_BEACON_ARGS --jwt-secret=$JWT_SECRET_FILE"
# 
#     # two cases, either seperate auth ports or one.
#     if [ -n "$EXECUTION_AUTH_PORT" ]; then
#         # we have same http/ws auth port.
#         ADDITIONAL_BEACON_ARGS="$ADDITIONAL_BEACON_ARGS --execution-provider=http://$HTTP_WEB3_IP_ADDR:$EXECUTION_AUTH_PORT"
#     else
#         # prysm currently supports http only for now.
#         if [ -n "$EXECUTION_AUTH_HTTP_PORT" ]; then
#             ADDITIONAL_BEACON_ARGS="$ADDITIONAL_BEACON_ARGS --execution-provider=http://$HTTP_WEB3_IP_ADDR:$EXECUTION_AUTH_HTTP_PORT"
#         else
#             ADDITIONAL_BEACON_ARGS="$ADDITIONAL_BEACON_ARGS --execution-provider=ws://$WS_WEB3_IP_ADDR:$EXECUTION_AUTH_WS_PORT"
#         fi
#     fi
# 
# else
#     # no auth.
#     if [ -n "$EXECUTION_ENGINE_PORT" ]; then
#         # we have same http/ws auth port.
#         ADDITIONAL_BEACON_ARGS="$ADDITIONAL_BEACON_ARGS --execution-provider=http://$HTTP_WEB3_IP_ADDR:$EXECUTION_ENGINE_PORT"
#     else
#         # prysm only does http
#         if [ -n "$EXECUTION_ENGINE_HTTP_PORT" ]; then
#             ADDITIONAL_BEACON_ARGS="$ADDITIONAL_BEACON_ARGS --execution-provider=http://$HTTP_WEB3_IP_ADDR:$EXECUTION_ENGINE_HTTP_PORT"
#         else
#             ADDITIONAL_BEACON_ARGS="$ADDITIONAL_BEACON_ARGS --execution-provider=ws://$WS_WEB3_IP_ADDR:$EXECUTION_ENGINE_WS_PORT"
#         fi
#     fi
# 
# fi

if [[ $PRESET_BASE == "minimal" ]]; then
    ADDITIONAL_BEACON_ARGS="$ADDITIONAL_BEACON_ARGS --minimal-config"
    ADDITIONAL_VALIDATOR_ARGS="$ADDITIONAL_VALIDATOR_ARGS --minimal-config"
fi

while [ ! -f "$CONSENSUS_CHECKPOINT_FILE" ]; do
    echo "waiting on consensus checkpoint file.."
    sleep 1
done

echo "prysm launching with additional-beacon-args: $ADDITIONAL_BEACON_ARGS"
echo "prysm launching with additional-validator-args: $ADDITIONAL_VALIDATOR_ARGS"

beacon-chain \
  $ADDITIONAL_BEACON_ARGS \
  --accept-terms-of-use=true \
  --datadir="$NODE_DIR" \
  --chain-config-file="$TESTNET_DIR/config.yaml" \
  --genesis-state="$TESTNET_DIR/genesis.ssz" \
  --bootstrap-node="$(< "$CONSENSUS_BOOTNODE_ENR_FILE")" \
  --verbosity="$PRYSM_DEBUG_LEVEL" \
  --p2p-host-ip="$IP_ADDR" \
  --p2p-max-peers="$CONSENSUS_TARGET_PEERS" \
  --p2p-udp-port="$CONSENSUS_P2P_PORT" --p2p-tcp-port="$CONSENSUS_P2P_PORT" \
  --monitoring-host=0.0.0.0 --monitoring-port="$BEACON_METRIC_PORT" \
  --rpc-host=0.0.0.0 --rpc-port="$BEACON_RPC_PORT" \
  --grpc-gateway-host=0.0.0.0 \
  --grpc-gateway-port="$BEACON_API_PORT" \
  --enable-debug-rpc-endpoints \
  --p2p-allowlist="$NETRESTRICT_RANGE" \
  --subscribe-all-subnets \
  --force-clear-db \
  --min-sync-peers 1 &

sleep 10

validator \
  --accept-terms-of-use=true \
  --datadir="$NODE_DIR" \
  --chain-config-file="$TESTNET_DIR/config.yaml" \
  --beacon-rpc-provider="127.0.0.1:$BEACON_RPC_PORT" \
  --monitoring-host=0.0.0.0 --monitoring-port="$VALIDATOR_METRIC_PORT" \
  --graffiti="prysm-kiln:$IP_ADDR" \
  --wallet-dir="$NODE_DIR" \
  --wallet-password-file="$TESTNET_DIR/wallet-password.txt" "$ADDITIONAL_VALIDATOR_ARGS"\
  --verbosity=debug 
