#!/bin/bash 
PRESET_BASE=$1
STARK_FORK=$2
END_FORK=$3
DEBUG_LEVEL=$4
TESTNET_DIR=$5
NODE_DATADIR=$6
WEB3_PROVIDER=$7
IP_ADDR=$8
P2P_PORT=$9
METRICS_PORT=${10}
RPC_PORT=${11}
GRPC_PORT=${12}
VALIDATOR_METRICS_PORT=${13}
GRAFFITI=${14}
NETRESTRICT_RANGE=${15}

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
    BEACON_ADDITIONAL_ARGS="--execution-provider=$WEB3_PROVIDER"
fi

if [[ $PRESET_BASE == "minimal" ]]; then
    ADDITIONAL_ARGS="--minimal-config"
fi

beacon-chain \
  --accept-terms-of-use=true \
  --verbosity="$DEBUG_LEVEL" \
  --log-file="$NODE_DATADIR/log.txt" \
  --subscribe-all-subnets \
  --datadir="$NODE_DATADIR" \
  --genesis-state="$TESTNET_DIR/genesis.ssz" \
  --chain-config-file="$TESTNET_DIR/config.yaml" \
  --http-web3provider="$WEB3_PROVIDER" \
  --bootstrap-node="$(< /data/local_testnet/bootnode/enr.dat)" \
  --p2p-max-peers=10 \
  --p2p-host-ip="$IP_ADDR" \
  --p2p-udp-port="$P2P_PORT" --p2p-tcp-port="$P2P_PORT" \
  --grpc-gateway-host=0.0.0.0 \
  --grpc-gateway-port="$GRPC_PORT" \
  --monitoring-host=0.0.0.0 --monitoring-port="$METRICS_PORT" \
  --rpc-host=0.0.0.0 --rpc-port="$RPC_PORT" \
  --enable-debug-rpc-endpoints \
  --p2p-allowlist="$NETRESTRICT_RANGE" \
  --enable-debug-rpc-endpoints $ADDITIONAL_ARGS $BEACON_ADDITIONAL_ARGS\
  --min-sync-peers 1 &

sleep 20

validator \
  --accept-terms-of-use=true $ADDITIONAL_ARGS \
  --minimal-config \
  --datadir="$NODE_DATADIR" \
  --beacon-rpc-provider="127.0.0.1:$RPC_PORT" \
  --beacon-rpc-gateway-provider="127.0.0.1:$GRPC_PORT" \
  --chain-config-file="$TESTNET_DIR/config.yaml" \
  --graffiti="$GRAFFITI" \
  --wallet-dir="$NODE_DATADIR" \
  --wallet-password-file="$TESTNET_DIR/wallet-password.txt" \
  --monitoring-host=0.0.0.0 --monitoring-port="$VALIDATOR_METRICS_PORT" \
  --verbosity=debug
