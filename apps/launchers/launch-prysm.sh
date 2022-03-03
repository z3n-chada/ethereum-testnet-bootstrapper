#!/bin/bash 
env_vars=( "PRESET_BASE", "START_FORK", "END_FORK", "DEBUG_LEVEL", "TESTNET_DIR", "NODE_DIR", "HTTP_WEB3_IP_ADDR", "IP_ADDR", "CONSENSUS_P2P_PORT", "BEACON_METRIC_PORT", "BEACON_RPC_PORT", "BEACON_API_PORT", "VALIDATOR_METRIC_PORT", "GRAFFITI", "NETRESTRICT_RANGE" , "EXECUTION_HTTP_PORT")

for var in "${env_vars[@]}" ; do
    if [[ -z "$var" ]]; then
        echo "$var not set"
        exit 1
    fi
done

ADDITIONAL_ARGS=""
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
    ADDITIONAL_ARGS="--minimal-config"
fi

if [[ -n "$EXECUTION_LAUNCHER" ]]; then
    "$EXECUTION_LAUNCHER" &
fi

beacon-chain \
  --accept-terms-of-use=true \
  --verbosity="$DEBUG_LEVEL" \
  --log-file="$NODE_DIR/log.txt" \
  --subscribe-all-subnets \
  --datadir="$NODE_DIR" \
  --genesis-state="$TESTNET_DIR/genesis.ssz" \
  --chain-config-file="$TESTNET_DIR/config.yaml" \
  --http-web3provider="http://$HTTP_WEB3_IP_ADDR:$EXECUTION_HTTP_PORT" \
  --bootstrap-node="$(< /data/local_testnet/bootnode/enr.dat)" \
  --p2p-max-peers=10 \
  --p2p-host-ip="$IP_ADDR" \
  --p2p-udp-port="$CONSENSUS_P2P_PORT" --p2p-tcp-port="$CONSENSUS_P2P_PORT" \
  --grpc-gateway-host=0.0.0.0 \
  --grpc-gateway-port="$BEACON_API_PORT" \
  --rpc-host=0.0.0.0 --rpc-port="$BEACON_RPC_PORT" \
  --monitoring-host=0.0.0.0 --monitoring-port="$BEACON_METRIC_PORT" \
  --enable-debug-rpc-endpoints \
  --p2p-allowlist="$NETRESTRICT_RANGE" \
  --enable-debug-rpc-endpoints $ADDITIONAL_ARGS $BEACON_ADDITIONAL_ARGS\
  --min-sync-peers 1 &

sleep 20

validator \
  --accept-terms-of-use=true $ADDITIONAL_ARGS \
  --minimal-config \
  --datadir="$NODE_DIR" \
  --beacon-rpc-provider="127.0.0.1:$BEACON_RPC_PORT" \
  --chain-config-file="$TESTNET_DIR/config.yaml" \
  --graffiti="$GRAFFITI" \
  --wallet-dir="$NODE_DIR" \
  --wallet-password-file="$TESTNET_DIR/wallet-password.txt" \
  --monitoring-host=0.0.0.0 --monitoring-port="$VALIDATOR_METRIC_PORT" \
  --verbosity=debug

  #--beacon-rpc-gateway-provider="127.0.0.1:$BEACON_API_PORT" \
