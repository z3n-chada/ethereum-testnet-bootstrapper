#!/bin/bash

env_vars=("CONFIG_FILE" "BOOTNODE_ENR" "EXECUTION_DATA_DIR" "EXECUTION_GENESIS" "NETWORK_ID" "EXECUTION_P2P_PORT" "EXECUTION_HTTP_PORT" "EXECUTION_WS_PORT" "HTTP_APIS" "WS_APIS" "IP_ADDR" "NETRESTRICT_RANGE" "END_FORK")

for var in "${env_vars[@]}" ; do
    if [[ -z "$var" ]]; then
        echo "$var not set"
        exit 1
    fi
done

mkdir -p EXECUTION_DATA_DIR

if [[ -n "$EXECUTION_LAUNCHER" ]]; then
    echo "tx-fuzzer launching execution client"
    ls "/data/"
    ls "/data/local_testnet/execution-bootstrapper/"
    "$EXECUTION_LAUNCHER" &
fi

private_keys=`python3 /source/apps/launchers/fuzzers/tx-fuzzer.py --config "$CONFIG_FILE" --action privateKeys`

public_keys=`python3 /source/apps/launchers/fuzzers/tx-fuzzer.py --config "$CONFIG_FILE" --action publicKeys`
echo "$private_keys"
echo "$public_keys"

sleep 60
./tx-fuzz.bin "http://$IP_ADDR:$EXECUTION_HTTP_PORT" spam "$private_keys" "$public_keys"
