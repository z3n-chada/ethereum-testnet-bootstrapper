env_vars=( 
    "EXECUTION_CHECKPOINT_FILE" 
    "IP_ADDR" 
    "EXECUTION_DATA_DIR" 
    "EXECUTION_HTTP_PORT" 
    "EXECUTION_WS_PORT" 
    "EXECUTION_P2P_PORT" 
    "NETWORK_ID" 
    "HTTP_APIS" 
    "WS_APIS" 
    "END_FORK_NAME" 
    "BESU_PRIVATE_KEY" 
    "EXECUTION_LOG_LEVEL"
    "BESU_GENESIS_FILE" 
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
    ###For the bootstrapper###TODO
    # CLIQUE_UNLOCK_KEY
    # IS_MINING
    # ETH1_PASSPHRASE

for var in "${env_vars[@]}" ; do
    if [[ -z "$var" ]]; then
        echo "$var not set"
        exit 1
    fi
done

echo "besu bootstrapper got a valid env-var set"

ADDITIONAL_ARGS="--logging=$EXECUTION_LOG_LEVEL"

if [[ "$END_FORK_NAME" = "bellatrix" ]]; then
    # since we are doing the merge in the consensus
    # we need to add the terminal total difficutly override
    echo "Besu client is taking part in a merge testnet, adding the required flags."
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --Xmerge-support=true"
    echo "Besu using --Xmerge-support"
else
    echo "Besu not overriding terminal total difficulty. Got an END_FORK:$END_FORK_NAME"
    echo "if you are trying to test a merge configuration check that the config file is sane"
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --Xmerge-support=false"
fi 

while [ ! -f "$EXECUTION_CHECKPOINT_FILE" ]; do
    sleep 1
    echo "Waiting on exeuction genesis"
done

if [ -n "$JWT_SECRET_FILE" ]; then
    echo "Besu is using JWT auth"
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --engine-jwt-enabled=true"
    # add the auth port for engine.
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --engine-rpc-http-port=$EXECUTION_AUTH_HTTP_PORT --engine-rpc-ws-port=$EXECUTION_AUTH_WS_PORT"
else
    echo "Besu is not using JWT auth"
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --rpc-http-authentication-enabled=false --rpc-ws-authentication-enabled=false --engine-jwt-enabled=false"
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --engine-rpc-http-port=$EXECUTION_ENGINE_HTTP_PORT --engine-rpc-ws-port=$EXECUTION_ENGINE_WS_PORT"
fi


echo "besu launching with additional args: $ADDITIONAL_ARGS"

besu \
  $ADDITIONAL_ARGS \
  --data-path="$EXECUTION_DATA_DIR" \
  --genesis-file="$BESU_GENESIS_FILE" \
  --network-id="$NETWORK_ID" \
  --rpc-http-enabled=true --rpc-http-api="$HTTP_APIS" \
  --rpc-http-host=0.0.0.0 \
  --rpc-http-port="$EXECUTION_HTTP_PORT" \
  --rpc-http-cors-origins="*" \
  --rpc-ws-enabled=true --rpc-ws-api="$WS_APIS" \
  --rpc-ws-host=0.0.0.0 \
  --rpc-ws-port="$EXECUTION_WS_PORT" \
  --host-allowlist="*" \
  --p2p-enabled=true \
  --p2p-host="$IP_ADDR" \
  --nat-method=DOCKER \
  --sync-mode=FULL \
  --engine-host-allowlist="*" \
  --fast-sync-min-peers=1 \
  --discovery-enabled=false \
  --p2p-port="$EXECUTION_P2P_PORT"
