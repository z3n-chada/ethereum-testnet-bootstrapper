
ADDITIONAL_ARGS="--logging=$EXECUTION_LOG_LEVEL"

while [ ! -f "$EXECUTION_CHECKPOINT_FILE" ]; do
    sleep 1
    echo "Waiting on exeuction genesis"
done

#--discovery-enabled=false \
#--discovery-dns-url="" \
#--Xmerge-support=true \
#--miner-coinbase="{{fee_recipient}}"
#--sync-mode=FULL \
besu \
  --logging="$EXECUTION_LOG_LEVEL" \
  --bootnodes="$EXECUTION_BOOTNODE" \
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
  --sync-mode=X_SNAP \
  --fast-sync-min-peers=1 \
  --p2p-port="$EXECUTION_P2P_PORT" \
  --engine-rpc-enabled=true \
  --engine-jwt-enabled \
  --engine-jwt-secret="$JWT_SECRET_FILE" \
  --engine-host-allowlist="*" \
  --engine-rpc-port="$EXECUTION_ENGINE_HTTP_PORT" 
