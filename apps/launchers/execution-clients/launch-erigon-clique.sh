#!/bin/bash

#"BOOTNODE_ENR" 
env_vars=( 
    "EXECUTION_CHECKPOINT_FILE"
    "IP_ADDR" 
    "EXECUTION_DATA_DIR" 
    "EXECUTION_HTTP_PORT" 
    "EXECUTION_WS_PORT" 
    "EXECUTION_P2P_PORT" 
    "HTTP_APIS" 
    "WS_APIS" 
    "NETWORK_ID" 
    "END_FORK_NAME" 
    "EXECUTION_LOG_LEVEL"
    "ERIGON_GENESIS_FILE" 
)

# OPTIONAL: 
    # TERMINAL_TOTAL_DIFFICULTY
    # EXECUTION_HTTP_ENGINE_PORT
    # EXECUTION_WS_ENGINE_PORT
    # EXECUTION_HTTP_AUTH_ENGINE_PORT
    # EXECUTION_WS_AUTH_ENGINE_PORT
    # EXECUTION_HTTP_AUTH_PORT
    # EXECUTION_WS_AUTH__PORT
    # JWT_SECRET_FILE
    # TX_FUZZ_ENABLED
    # NETRESTRICT_RANGE
    # MAX_PEERS
    ###For the bootstrapper###
    # GETH_PASSWORD_FILE
    # CLIQUE_UNLOCK_KEY
    # IS_MINING
    # ETH1_PASSPHRASE



for var in "${env_vars[@]}" ; do
    if [[ -z "${!var}" ]]; then
        echo "$var not set"
        exit 1
    fi
done

echo "erigon got a valid env-var set"

ADDITIONAL_ARGS="--verbosity=$EXECUTION_LOG_LEVEL"

echo "Lauching erigon-execution client"

while [ ! -f "/data/erigon-execution-clients-ready" ]; do
    sleep 1
    echo "Waiting on erigon execution genesis."
done

echo "Detected execution genesis"
static_nodes=`cat /data/execution-enodes.txt`
echo "erigon using static peers: $static_nodes"
echo "Initing the genesis"
erigon init \
    --datadir "$EXECUTION_DATA_DIR" \
    "$ERIGON_GENESIS_FILE"


if [ "$IS_MINING" = "true" ]; then
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --mine"
fi

if [ "$TX_FUZZ_ENABLED" = "true" ]; then
    $TX_FUZZ_LAUNCHER &
fi

# geth is either the bootnode, or it should use the bootnode.
if [ -n "$EXECUTION_BOOTNODE_PRIVATE_KEY" ]; then
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --nodekeyhex=$EXECUTION_BOOTNODE_PRIVATE_KEY"
else
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --nodekey=$EXECUTION_DATA_DIR/nodekey.txt"
fi
if [ -n "$EXECUTION_BOOTNODE" ]; then
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --bootnodes=$EXECUTION_BOOTNODE"
fi

echo "Starting erigon with additional args: $ADDITIONAL_ARGS"

echo "execution engine port: $EXECUTION_ENGINE_HTTP_PORT"

erigon \
  --datadir="$EXECUTION_DATA_DIR" \
  --discovery.dns="" \
  --networkid="$NETWORK_ID" \
  --port "$EXECUTION_P2P_PORT" \
  --nat "extip:$IP_ADDR" \
  --http --http.api "$HTTP_APIS" \
  --http.port "$EXECUTION_HTTP_PORT" \
  --http.addr 0.0.0.0 \
  --http.corsdomain "*" \
  --ws \
  --allow-insecure-unlock \
  --netrestrict="$NETRESTRICT_RANGE" \
  --prune=htrc \
  --authrpc.port="$EXECUTION_ENGINE_HTTP_PORT" \
  --authrpc.addr=0.0.0.0 \
  --authrpc.jwtsecret="$JWT_SECRET_FILE" \
  --staticpeers="$static_nodes" $ADDITIONAL_ARGS
