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
    "GETH_GENESIS_FILE" 
    "GETH_EXECUTION_GENESIS"
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

echo "geth got a valid env-var set"

ADDITIONAL_ARGS="--verbosity=$EXECUTION_LOG_LEVEL"

echo "Lauching geth-execution client"

while [ ! -f "/data/execution-clients-ready" ]; do
    sleep 1
    echo "Waiting on exeuction genesis"
done

echo "Detected execution genesis"

echo "Initing the genesis"
geth init \
    --datadir "$EXECUTION_DATA_DIR" \
    "$GETH_GENESIS_FILE"


if [ -n "$GETH_PASSWORD_FILE" ]; then
    echo "$ETH1_PASSPHRASE" > "$GETH_PASSWORD_FILE"
fi

if [ -n "$CLIQUE_UNLOCK_KEY" ]; then
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --unlock=$CLIQUE_UNLOCK_KEY --password=/data/geth-account-passwords.txt"
fi

if [ "$IS_MINING" = "true" ]; then
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --mine"
fi

if [ "$TX_FUZZ_ENABLED" = "true" ]; then
    $TX_FUZZ_LAUNCHER &
fi

# geth is either the bootnode, or it should use the bootnode.
if [ -n "$EXECUTION_BOOTNODE_PRIVATE_KEY" ]; then
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --nodekeyhex=$EXECUTION_BOOTNODE_PRIVATE_KEY"
elif [ -n "$EXECUTION_BOOTNODE" ]; then
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --bootnodes=$EXECUTION_BOOTNODE"
fi

echo "Starting geth"
echo "Starting geth with additional args: $ADDITIONAL_ARGS"

geth \
  --datadir="$EXECUTION_DATA_DIR" \
  --discovery.dns="" \
  --networkid="$NETWORK_ID" \
  --port "$EXECUTION_P2P_PORT" \
  --nat "extip:$IP_ADDR" \
  --http --http.api "$HTTP_APIS" \
  --http.port "$EXECUTION_HTTP_PORT" \
  --http.addr 0.0.0.0 \
  --http.corsdomain "*" \
  --ws --ws.api "$WS_APIS" \
  --ws.port="$EXECUTION_WS_PORT" \
  --ws.addr 0.0.0.0 \
  --keystore '/source/apps/data/geth-keystores/' \
  --rpc.allow-unprotected-txs \
  --allow-insecure-unlock \
  --netrestrict="$NETRESTRICT_RANGE" \
  --syncmode=full \
  --authrpc.vhosts="*" \
  --authrpc.port="$EXECUTION_ENGINE_HTTP_PORT" \
  --authrpc.addr=0.0.0.0 \
  --authrpc.jwtsecret="$JWT_SECRET_FILE" \
  --vmodule=rpc=5 \
  --override.terminaltotaldifficulty="$TERMINAL_TOTAL_DIFFICULTY" $ADDITIONAL_ARGS
