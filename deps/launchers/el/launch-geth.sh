#!/bin/bash


# Additional args is used so the bootstrapper and standard instances can use
# the same launcher.
ADDITIONAL_ARGS="--verbosity=$EXECUTION_LOG_LEVEL"

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
    "EXECUTION_LOG_LEVEL"
    "GETH_GENESIS_FILE" 
    "GETH_EXECUTION_GENESIS"
    "JWT_SECRET_FILE"
    "NETRESTRICT_RANGE"
)

# OPTIONAL:
    # EXECUTION_HTTP_ENGINE_PORT
    # EXECUTION_WS_ENGINE_PORT
    # EXECUTION_HTTP_AUTH_ENGINE_PORT
    # EXECUTION_WS_AUTH_ENGINE_PORT
    # EXECUTION_HTTP_AUTH_PORT
    # EXECUTION_WS_AUTH__PORT
    # TX_FUZZ_ENABLED -> this is for running the tx-spammer.

    ###For the bootstrapper###
    # GETH_PASSWORD_FILE
    # ETH1_PASSPHRASE



# verify vars we need are set and available.
for var in "${env_vars[@]}" ; do
    if [[ -z "$var" ]]; then
        echo "GETH error in geth var check."
        echo "$var not set"
        exit 1
    fi
done


# wait for the signal from the bootstrapper that EL clients can come online.
while [ ! -f "/data/execution-clients-ready" ]; do
    sleep 1
    echo "Waiting on exeuction genesis"
done
echo "Detected execution genesis"

# go geth init
echo "GETH: Init the genesis"
geth init \
    --datadir "$EXECUTION_DATA_DIR" \
    "$GETH_GENESIS_FILE"

#if [ -n "$GETH_PASSWORD_FILE" ]; then
#    echo "$ETH1_PASSPHRASE" > "$GETH_PASSWORD_FILE"
#fi

#if [ "$TX_FUZZ_ENABLED" = "true" ]; then
#    $TX_FUZZ_LAUNCHER &
#fi
#
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
  --networkid="$NETWORK_ID" \
  --port "$EXECUTION_P2P_PORT" \
  --http --http.api "$HTTP_APIS" \
  --http.port "$EXECUTION_HTTP_PORT" \
  --http.addr 0.0.0.0 \
  --http.corsdomain "*" \
  --http.vhosts="*" \
  --ws --ws.api "$WS_APIS" \
  --ws.port="$EXECUTION_WS_PORT" \
  --ws.addr 0.0.0.0 \
  --gcmode=archive \
  --authrpc.port="$EXECUTION_ENGINE_HTTP_PORT" \
  --authrpc.addr=0.0.0.0 \
  --authrpc.vhosts="*" \
  --authrpc.jwtsecret="$JWT_SECRET_FILE" \
  --nat "extip:$IP_ADDR" \
  --rpc.allow-unprotected-txs \
  --allow-insecure-unlock \
  --netrestrict="$NETRESTRICT_RANGE" \
  --syncmode=full \
  --vmodule=rpc=5 \
  --keystore '/source/apps/data/geth-keystores/' \
  --discovery.dns="" $ADDITIONAL_ARGS