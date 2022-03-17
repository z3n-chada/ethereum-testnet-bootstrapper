#!/bin/bash 
env_vars=( "PRESET_BASE", "START_FORK", "END_FORK", "DEBUG_LEVEL", "TESTNET_DIR", "NODE_DIR", "HTTP_WEB3_IP_ADDR", "IP_ADDR", "CONSENSUS_P2P_PORT", "BEACON_METRIC_PORT", "BEACON_RPC_PORT", "BEACON_API_PORT", "VALIDATOR_METRIC_PORT", "GRAFFITI", "NETRESTRICT_RANGE" , "EXECUTION_HTTP_PORT")

for var in "${env_vars[@]}" ; do
    if [[ -z "$var" ]]; then
        echo "$var not set"
        exit 1
    fi
done

ADDITIONAL_ARGS="--accept-terms-of-use=true"
BEACON_ADDITIONAL_ARGS=""

while [ ! -f "/data/consensus-clients-ready" ]; do
    sleep 1
done

while [ ! -f "/data/local_testnet/bootnode/enr.dat" ]; do
    echo "waiting on bootnode"
    sleep 1
done

if [[ $END_FORK == "bellatrix" ]]; then
    BEACON_ADDITIONAL_ARGS="--execution-provider=http://$HTTP_WEB3_IP_ADDR:$EXECUTION_HTTP_PORT"
fi

if [[ $PRESET_BASE == "minimal" ]]; then
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --minimal-config"
fi

if [[ -n "$EXECUTION_LAUNCHER" ]]; then
    "$EXECUTION_LAUNCHER" &
fi

beacon-chain \
  "$ADDITIONAL_ARGS" \
  --datadir="$NODE_DIR" \
  --chain-config-file="$TESTNET_DIR/config.yaml" \
  --genesis-state="$TESTNET_DIR/genesis.ssz" \
  --http-web3provider="http://$HTTP_WEB3_IP_ADDR:$EXECUTION_HTTP_PORT" \
  --bootstrap-node="$(< /data/local_testnet/bootnode/enr.dat)" \
  --verbosity="$DEBUG_LEVEL" \
  --log-file="$NODE_DIR/log.txt" \
  --p2p-host-ip="$IP_ADDR" \
  --p2p-max-peers=10 \
  --p2p-udp-port="$CONSENSUS_P2P_PORT" --p2p-tcp-port="$CONSENSUS_P2P_PORT" \
  --monitoring-host=0.0.0.0 --monitoring-port="$BEACON_METRIC_PORT" \
  --rpc-host=0.0.0.0 --rpc-port="$BEACON_RPC_PORT" \
  --grpc-gateway-host=0.0.0.0 \
  --grpc-gateway-port="$BEACON_API_PORT" \
  --enable-debug-rpc-endpoints "$BEACON_ADDITIONAL_ARGS" \
  --p2p-allowlist="$NETRESTRICT_RANGE" \
  --subscribe-all-subnets \
  --min-sync-peers 1 &

sleep 10

validator \
  "$ADDITIONAL_ARGS" \
  --datadir="$NODE_DIR" \
  --chain-config-file="$TESTNET_DIR/config.yaml" \
  --beacon-rpc-provider="127.0.0.1:$BEACON_RPC_PORT" \
  --monitoring-host=0.0.0.0 --monitoring-port="$VALIDATOR_METRIC_PORT" \
  --graffiti="prysm-kiln:$IP_ADDR" \
  --wallet-dir="$NODE_DIR" \
  --wallet-password-file="$TESTNET_DIR/wallet-password.txt" \
  --verbosity=debug

