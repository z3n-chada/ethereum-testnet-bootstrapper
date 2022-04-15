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
    if [[ -z "$var" ]]; then
        echo "$var not set"
        exit 1
    fi
done

echo "geth got a valid env-var set"

ADDITIONAL_ARGS="--verbosity=$EXECUTION_LOG_LEVEL"

if [[ "$END_FORK_NAME" = "bellatrix" ]]; then
    # since we are doing the merge in the consensus
    # we need to add the terminal total difficutly override
    echo "Geth client is taking part in a merge testnet, overriding the TTD"
    if [[ -z "$TERMINAL_TOTAL_DIFFICULTY" ]]; then
        echo "We are doing a merge consensus test but no terminal total difficulty was applied"
        exit 1
    fi
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --override.terminaltotaldifficulty=$TERMINAL_TOTAL_DIFFICULTY"
    echo "Geth is overriding terminaltotaldifficulty"
else
    echo "Geth not overriding terminal total difficulty. Got an END_FORK:$END_FORK_NAME"
    echo "if you are trying to test a merge configuration check that the config file is sane"
fi 

echo "Lauching execution client"

while [ ! -f "/data/execution-clients-ready" ]; do
    sleep 1
    echo "Waiting on exeuction genesis"
done

echo "Detected execution genesis"

echo "Initing the genesis"
geth init \
    --datadir "$EXECUTION_DATA_DIR" \
    "$GETH_GENESIS_FILE"

# not implemented.
if [ -n "$JWT_SECRET_FILE" ]; then
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --authrpc.port=$EXECUTION_AUTH_HTTP_PORT --authrpc.addr=0.0.0.0 --authrpc.jwtsecret=$JWT_SECRET_FILE"
    echo "Geth is using JWT"
fi

if [ -n "$GETH_PASSWORD_FILE" ]; then
    echo "$ETH1_PASSPHRASE" > "$GETH_PASSWORD_FILE"
fi

if [ -n "$CLIQUE_UNLOCK_KEY" ]; then
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --unlock=$CLIQUE_UNLOCK_KEY --password=/data/geth-account-passwords.txt"
fi

if [ -n "$IS_MINING" ]; then
    if $IS_MINING; then
        ADDITIONAL_ARGS="$ADDITIONAL_ARGS --mine"
    fi
fi

if [ -n "$TX_FUZZ_ENABLED" ]; then
    if $TX_FUZZ_ENABLED; then
        $TX_FUZZ_LAUNCHER &
    fi
fi

echo "Starting geth"
echo "Starting geth with additional args: $ADDITIONAL_ARGS"

geth \
  --datadir="$EXECUTION_DATA_DIR" \
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
  --maxpeers=200 \
  --syncmode=full \
  --authrpc.vhosts="*" \
  --vmodule=rpc=5 $ADDITIONAL_ARGS

  # --v5disc \
