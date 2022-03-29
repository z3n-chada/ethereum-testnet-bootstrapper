env_vars=( "EXECUTION_DATA_DIR" "BESU_GENESIS_FILE" "NETWORK_ID" "EXECUTION_P2P_PORT" "EXECUTION_HTTP_PORT" "EXECUTION_WS_PORT" "HTTP_APIS" "WS_APIS" "IP_ADDR" "NETRESTRICT_RANGE" "END_FORK_NAME" "EXECUTION_ENGINE_PORT" "BESU_PRIVATE_KEY" "CONSENSUS_TARGET_PEERS" "EXECUTION_CHECKPOINT_FILE")

for var in "${env_vars[@]}" ; do
    if [[ -z "$var" ]]; then
        echo "$var not set"
        exit 1
    fi
done

echo "besu bootstrapper got a valid env-var set"

MERGE_ARGS=""

if [[ "$END_FORK_NAME" = "bellatrix" ]]; then
    # since we are doing the merge in the consensus
    # we need to add the terminal total difficutly override
    echo "Besu client is taking part in a merge testnet, adding the required flags."
    MERGE_ARGS="--Xmerge-support=true"
    echo "using $MERGE_ARGS"
else
    echo "Geth not overriding terminal total difficulty. Got an END_FORK:$END_FORK_NAME"
    echo "if you are trying to test a merge configuration check that the config file is sane"
    MERGE_ARGS="--Xmerge-support=false"
fi 

while [ ! -f "$EXECUTION_CHECKPOINT_FILE" ]; do
    sleep 1
    echo "Waiting on exeuction genesis"
done

# while [ ! -f "/data/local_testnet/execution-bootstrapper/enodes.txt" ]; do
#     sleep 1
#     echo "Waiting on the enodes /data/local_testnet/execution-bootstrapper/enodes.txt"
# done
# #
# echo "found enodes"
# ENODES=`cat /data/local_testnet/execution-bootstrapper/enodes.txt | tr -d "\n"`
# echo $ENODES
#get the bootnode we are going to use.

# --bootnodes="$ENODES" \
besu \
  --data-path="$EXECUTION_DATA_DIR" \
  --genesis-file="$BESU_GENESIS_FILE" \
  --network-id="$NETWORK_ID" \
  --rpc-http-enabled=true --rpc-http-api="$HTTP_APIS" \
  --rpc-http-host=0.0.0.0 \
  --rpc-http-port="$EXECUTION_HTTP_PORT" \
  --engine-rpc-http-port="$EXECUTION_ENGINE_PORT" \
  --engine-host-allowlist="*" \
  --rpc-http-cors-origins="*" \
  --rpc-ws-enabled=true --rpc-ws-api="$WS_APIS" \
  --rpc-ws-host=0.0.0.0 \
  --rpc-ws-port="$EXECUTION_WS_PORT" \
  --host-allowlist="*" \
  --p2p-enabled=true \
  --p2p-host="$IP_ADDR" \
  --nat-method=DOCKER \
  --sync-mode=FULL \
  --fast-sync-min-peers=2 \
  --Xmerge-support=true \
  --p2p-port="$EXECUTION_P2P_PORT"
 
