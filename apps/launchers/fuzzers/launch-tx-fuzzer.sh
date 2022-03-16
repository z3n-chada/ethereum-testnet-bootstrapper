#!/bin/bash
env_vars=("CONFIG_FILE" "PRESET_BASE" "START_FORK" "END_FORK" "DEBUG_LEVEL" "TESTNET_DIR" "NODE_DIR" "HTTP_WEB3_IP_ADDR" "EXECUTION_HTTP_PORT" "IP_ADDR" "CONSENSUS_P2P_PORT" "BEACON_API_PORT" "BEACON_METRIC_PORT")
for var in "${env_vars[@]}" ; do
    if [[ -z "$var" ]]; then
        echo "$var not set"
        exit 1
    fi
done

/source/apps/launchers/consensus-clients/launch-teku.sh & 

private_keys=`python3 /source/apps/launchers/fuzzers/tx-fuzzer.py --config "$CONFIG_FILE" --action privateKeys`
public_keys=`python3 /source/apps/launchers/fuzzers/tx-fuzzer.py --config "$CONFIG_FILE" --action publicKeys`
echo "tx-fuzzer using private-keys: $private_keys"
echo "tx-fuzzer using pub-keys: $public_keys"

sleep 60
./tx-fuzz.bin "http://$IP_ADDR:$EXECUTION_HTTP_PORT" spam "$private_keys" "$public_keys"
