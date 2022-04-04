env_vars=( "EXECUTION_DATA_DIR" "BESU_GENESIS_FILE" "NETWORK_ID" "EXECUTION_P2P_PORT" "EXECUTION_HTTP_PORT" "EXECUTION_WS_PORT" "HTTP_APIS" "WS_APIS" "IP_ADDR" "NETRESTRICT_RANGE" "END_FORK_NAME" "EXECUTION_ENGINE_PORT" "BESU_PRIVATE_KEY" "CONSENSUS_TARGET_PEERS" "EXECUTION_CHECKPOINT_FILE" "EXECUTION_LOG_LEVEL")

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

# --config=goerli_shadowfork
nethermind \
  --datadir="$EXECUTION_DATA_DIR" \
  --Init.ChainSpecPath="$NETHERMIND_GENESIS_FILE" \
  --Init.WebSocketsEnabled=true \
  --JsonRpc.Enabled=true \
  --JsonRpc.EnabledModules="net,eth,consensus,subscribe,web3,admin" \
  --JsonRpc.Port="$EXECUTION_HTTP_PORT" \
  --JsonRpc.WebSocketsPort="$EXECUTION_WS_PORT" \
  --JsonRpc.Host=0.0.0.0 \
  --Network.DiscoveryPort="$EXECUTION_P2P_PORT" \
  --Network.P2PPort="$EXECUTION_P2P_PORT" \
  --Merge.Enabled=true \
  --Merge.FeeRecipient="0xf97e180c050e5Ab072211Ad2C213Eb5AEE4DF134" \
  --Merge.TerminalTotalDifficulty=$"TOTAL_TERMINAL_DIFFICULTY" \
  --Init.DiagnosticMode="None" \
  --Init.IsMining=true \
  --JsonRpc.AdditionalRpcUrls="http://0.0.0.0:$EXECUTION_ENGINE_PORT|http;ws|net;eth;subscribe;engine;web3;client|no-auth" 
