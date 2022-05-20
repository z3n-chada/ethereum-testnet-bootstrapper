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

while [ ! -f "$EXECUTION_CHECKPOINT_FILE" ]; do
    sleep 1
    echo "Waiting on exeuction genesis"
done

# if [ -n "$JWT_SECRET_FILE" ]; then
#     echo "Besu is using JWT auth"
#     ADDITIONAL_ARGS="$ADDITIONAL_ARGS --engine-jwt-enabled=true"
#     # add the auth port for engine.
#     ADDITIONAL_ARGS="$ADDITIONAL_ARGS --engine-rpc-http-port=$EXECUTION_ENGINE_HTTP_PORT --engine-rpc-ws-port=$EXECUTION_ENGINE_WS_PORT"
# # else
# #     echo "Besu is not using JWT auth"
# #     ADDITIONAL_ARGS="$ADDITIONAL_ARGS --rpc-http-authentication-enabled=false --rpc-ws-authentication-enabled=false --engine-jwt-enabled=false"
# #     ADDITIONAL_ARGS="$ADDITIONAL_ARGS --engine-rpc-http-port=$EXECUTION_ENGINE_HTTP_PORT --engine-rpc-ws-port=$EXECUTION_ENGINE_WS_PORT"
# # fi
# fi


#echo "besu launching with additional args: $ADDITIONAL_ARGS"

  #--discovery-enabled=false \

besu \
  --logging="$EXECUTION_LOG_LEVEL" \
  --bootnodes="$EXECUTION_BOOTNODE" \
  --data-path="$EXECUTION_DATA_DIR" \
  --genesis-file="$BESU_GENESIS_FILE" \
  --discovery-dns-url="" \
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
  --Xmerge-support=true \
  --fast-sync-min-peers=1 \
  --p2p-port="$EXECUTION_P2P_PORT" \
  --engine-jwt-enabled=true \
  --engine-jwt-secret="$JWT_SECRET_FILE" \
  --engine-rpc-http-port="$EXECUTION_ENGINE_HTTP_PORT" \
  --engine-rpc-ws-port="$EXECUTION_ENGINE_WS_PORT"
