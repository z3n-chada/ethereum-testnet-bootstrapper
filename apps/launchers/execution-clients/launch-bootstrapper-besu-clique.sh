#!/bin/bash

env_vars=( "EXECUTION_DATA_DIR" "BESU_EXECUTION_GENESIS" "NETWORK_ID" "EXECUTION_P2P_PORT" "EXECUTION_HTTP_PORT" "EXECUTION_WS_PORT" "HTTP_APIS" "WS_APIS" "IP_ADDR" "NETRESTRICT_RANGE" "END_FORK" "EXECUTION_ENGINE_PORT" "BESU_PRIVATE_KEY" "EXECUTION_LOG_LEVEL")

for var in "${env_vars[@]}" ; do
    if [[ -z "${!var}" ]]; then
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

while [ ! -f "/data/execution-clients-ready" ]; do
    sleep 1
    echo "Waiting on exeuction genesis"
done

# besu is fickle. add the private key to the data dir.
echo "$BESU_PRIVATE_KEY" > "/tmp/key"

if [ -n "$JWT_SECRET_FILE" ]; then
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --rpc-http-authentication-enabled=true --rpc-ws-authentication-enabled=true --engine-jwt-enabled=true"
    echo "Besu is using JWT auth"
else
    ADDITIONAL_ARGS="$ADDITIONAL_ARGS --rpc-http-authentication-enabled=false --rpc-ws-authentication-enabled=false --engine-jwt-enabled=false"
    echo "Besu is not using JWT auth"
fi


besu \
  --data-path="$EXECUTION_DATA_DIR" \
  --genesis-file="$BESU_EXECUTION_GENESIS" \
  --network-id="$NETWORK_ID" \
  --node-private-key-file="/tmp/key" \
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
  --discovery-enabled=false $ADDITIONAL_ARGS \
  --p2p-port="$EXECUTION_P2P_PORT"
 
#--bootnodes="{{ eth1_bootnode_enode | join(',') }}"
