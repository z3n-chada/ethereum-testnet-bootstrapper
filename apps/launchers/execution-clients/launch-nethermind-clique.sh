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

# TODO: engine and jwt_secret_file
  # --JsonRpc.JwtSecretFile="$JWT_SECRET_FILE" \
  # --Sync.FastBlocks=true \
  # --Sync.FastSync=true \
  # --Sync.DownloadBodiesInFastSync=true \
  # --Sync.DownloadReceiptsInFastSync=true \
  # --Sync.UseGethLimitsInFastBlocks=true \
  # --Sync.PivotNumber=0 \
  # --Sync.PivotTotalDifficulty=1 \
  # --JsonRpc.AdditionalRpcUrls="http://localhost:$EXECUTION_ENGINE_AUTH_PORT|http|net;eth;subscribe;engine;web3;client|no-auth,http://localhost:$EXECUTION_ENGINE_WS_PORT|ws|net;eth;subscribe;engine;web3;client,http://localhost:$EXECUTION_ENGINE_PORT|http;ws|net;eth;subscribe;engine;web3;client|no-auth"

if [ -n "$JWT_SECRET_FILE" ]; then
    echo "Nethermind is using JWT auth"
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --JsonRpc.JwtSecretFile=$JWT_SECRET_FILE --JsonRpc.AdditionalRpcUrls=http://localhost:$EXECUTION_AUTH_HTTP_PORT|http;ws|net;eth;subscribe;engine;web3;client;clique,http://localhost:$EXECUTION_AUTH_WS_PORT|http;ws|net;eth;subscribe;engine;web3;client"

else
    echo "Nethermind is not using JWT auth"
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --JsonRpc.AdditionalRpcUrls=http://localhost:$EXECUTION_ENGINE_HTTP_PORT|http|net;eth;subscribe;engine;web3;client;clique|no-auth,http://localhost:$EXECUTION_ENGINE_WS_PORT|ws|net;eth;subscribe;engine;web3;client|no-auth --JsonRpc.UnsecureDevNoRpcAuthentication=True"
fi

echo "{}" > /tmp/nethermind.cfg
nethermind \
  $ADDITIONAL_ARGS \
  --config="/tmp/nethermind.cfg" \
  --datadir="$EXECUTION_DATA_DIR" \
  --Init.ChainSpecPath="$NETHER_MIND_GENESIS_FILE" \
  --Init.IsMining=true \
  --Init.StoreReceipts=true \
  --Init.WebSocketsEnabled=true \
  --Init.EnableUnsecuredDevWallet=true \
  --Init.DiagnosticMode="None" \
  --JsonRpc.Enabled=true \
  --JsonRpc.EnabledModules="$HTTP_APIS" \
  --JsonRpc.Port="$EXECUTION_HTTP_PORT" \
  --JsonRpc.WebSocketsPort="$EXECUTION_WS_PORT" \
  --JsonRpc.Host=0.0.0.0 \
  --Network.ExternalIp="$IP_ADDR" \
  --Network.LocalIp="$IP_ADDR" \
  --Network.DiscoveryPort="$EXECUTION_P2P_PORT" \
  --Network.P2PPort="$EXECUTION_P2P_PORT" \
  --Merge.Enabled=true \
  --Merge.FeeRecipient="0xf97e180c050e5Ab072211Ad2C213Eb5AEE4DF134" \
  --Merge.TerminalTotalDifficulty="$TERMINAL_TOTAL_DIFFICULTY"
