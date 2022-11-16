#!/bin/bash
env_vars=("EXECUTION_LAUNCHER" "HTTP_WEB3_IP_ADDR" "EXECUTION_HTTP_PORT" "EXECUTION_DATA_DIR" "EXECUTION_HTTP_PORT" "EXECUTION_LAUNCHER" "TX_FUZZ_ENABLED" "TX_FUZZ_PRIVATE_KEYS" "TX_FUZZ_PUBLIC_KEYS" "TX_FUZZ_MODE" "TX_FUZZ_ENABLED" "LAUNCH_NEW_EXECUTION_CLIENT")
for var in "${env_vars[@]}" ; do
    if [[ -z "${!var}" ]]; then
        echo "$var not set"
        exit 1
    fi
done

if "$LAUNCH_NEW_EXECUTION_CLIENT"; then
    echo "tx-fuzzer launching execution client: $EXECUTION_LAUNCHER"
    "$EXECUTION_LAUNCHER" &
fi

sleep 30

tx-fuzz "http://$HTTP_WEB3_IP_ADDR:$EXECUTION_HTTP_PORT" "$TX_FUZZ_MODE" "$TX_FUZZ_PRIVATE_KEYS" "$TX_FUZZ_PUBLIC_KEYS"
