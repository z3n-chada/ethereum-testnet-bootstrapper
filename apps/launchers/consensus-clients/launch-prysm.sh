#!/bin/bash 

if [[ -n "$EXECUTION_LAUNCHER" ]]; then
    "$EXECUTION_LAUNCHER" &
fi

while [ ! -f "$CONSENSUS_BOOTNODE_ENR_FILE" ]; do
    echo "waiting on bootnode"
    sleep 1
done

bootnode_enr=`cat $CONSENSUS_BOOTNODE_ENR_FILE`

while [ ! -f "$CONSENSUS_CHECKPOINT_FILE" ]; do
    echo "waiting on consensus checkpoint file.."
    sleep 1
done

#--force-clear-db \ for auto-resume to work we don't want to blow this away.
beacon-chain \
  --log-file="$NODE_DIR/beacon.log" \
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
  --jwt-secret="$JWT_SECRET_FILE" \
  --http-web3provider="http://$HTTP_WEB3_IP_ADDR:$EXECUTION_ENGINE_HTTP_PORT" \
  --min-sync-peers 1 \
  --enable-forkchoice-doubly-linked-tree \
  --enable-vectorized-htr &

sleep 10

validator \
  --log-file="$NODE_DIR/validator.log" \
  --accept-terms-of-use=true \
  --datadir="$NODE_DIR" \
  --chain-config-file="$TESTNET_DIR/config.yaml" \
  --beacon-rpc-provider="127.0.0.1:$BEACON_RPC_PORT" \
  --monitoring-host=0.0.0.0 --monitoring-port="$VALIDATOR_METRIC_PORT" \
  --graffiti="prysm-kiln:$IP_ADDR" \
  --wallet-dir="$NODE_DIR" \
  --wallet-password-file="$TESTNET_DIR/wallet-password.txt" \
  --verbosity=debug 
