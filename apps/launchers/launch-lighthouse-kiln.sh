#!/bin/bash

env_vars=( "PRESET_BASE", "START_FORK", "END_FORK", "DEBUG_LEVEL", "TESTNET_DIR", "NODE_DIR", "HTTP_WEB3_IP_ADDR", "IP_ADDR", "CONSENSUS_P2P_PORT", "BEACON_METRIC_PORT", "BEACON_RPC_PORT", "BEACON_API_PORT", "VALIDATOR_METRIC_PORT", "GRAFFITI", "NETRESTRICT_RANGE" , "EXECUTION_HTTP_PORT", "TOTALTERMINALDIFFICULTY", "CONSENSUS_TARGET_PEERS", "VALIDATOR_RPC_PORT")

for var in "${env_vars[@]}" ; do
    if [[ -z "$var" ]]; then
        echo "$var not set"
        exit 1
    fi
done

ADDITIONAL_ARGS=""

while [ ! -f "/data/consensus-clients-ready" ]; do
    sleep 1
done

while [ ! -f "/data/local_testnet/bootnode/enr.dat" ]; do
    echo "waiting on bootnode"
    sleep 1
done

if [ ! -f "$TESTNET_DIR/boot_enr.yaml" ]; then
    bootnode_enr=`cat /data/local_testnet/bootnode/enr.dat`
    echo "- $bootnode_enr" > $TESTNET_DIR/boot_enr.yaml
fi

# launch the local exectuion client
if [[ -n "$EXECUTION_LAUNCHER" ]]; then
    echo "lightouse-$IP_ADDR lauching a local execution client"
    "$EXECUTION_LAUNCHER" &
fi

# beacon_start_args: >
#   lighthouse
#   --debug-level="{{ beacon_log_level | lower }}"
#   --datadir "/beacondata"
#   --testnet-dir="/custom_config_data"
#   bn
#   --disable-enr-auto-update
#   --enr-address={{ansible_host}}
#   --enr-tcp-port={{beacon_p2p_port}} --enr-udp-port={{beacon_p2p_port}}
#   --port={{beacon_p2p_port}} --discovery-port={{beacon_p2p_port}}
#   --eth1
#   {% if (bootnode_enrs is defined) and bootnode_enrs %}
#   --boot-nodes="{{ bootnode_enrs | join(',') }}"
#   {% endif %}  --http
#   --http-address=0.0.0.0
#   --http-port="{{beacon_api_port}}"
#   --metrics
#   --metrics-address=0.0.0.0
#   --metrics-port="{{beacon_metrics_port}}"
#   --listen-address=0.0.0.0
#   --graffiti="{{graffiti}}"
#   --target-peers={{hi_peer_count}}
#   --http-allow-sync-stalled
#   --merge
#   --disable-packet-filter
#   --execution-endpoints={{execution_engine_endpoint}}
#   --eth1-endpoints={{eth1endpoint}}
#   --terminal-total-difficulty-override={{terminal_total_difficulty}}
#   --validator-monitor-auto
# # in case of eth1 deposit endpoint problems: --dummy-eth1
# 
# validator_start_args: >
#   lighthouse
#   --testnet-dir="/custom_config_data"
#   vc
#   --validators-dir="/validatordata/validators"
#   --secrets-dir="/validatordata/secrets"
#   --init-slashing-protection
#   --server={{beacon_endpoint}}
#   --graffiti="{{graffiti}}"
#   --http --http-port={{validator_rpc_port}}
#   --metrics --metrics-address 0.0.0.0 --metrics-port "{{validator_metrics_port}}"

# --boot-nodes "$bootnode_enr" \
lighthouse \
	--debug-level=$DEBUG_LEVEL \
	--datadir=$NODE_DIR \
	--testnet-dir $TESTNET_DIR \
	bn \
    --disable-enr-auto-update \
	--enr-address "$IP_ADDR" \
	--enr-udp-port "$CONSENSUS_P2P_PORT" --enr-tcp-port "$CONSENSUS_P2P_PORT" \
	--port="$CONSENSUS_P2P_PORT" --discovery-port "$CONSENSUS_P2P_PORT" \
    --eth1 \
	--http \
	--http-address=0.0.0.0 \
	--http-port="$BEACON_API_PORT" \
    --metrics \
    --metrics-address=0.0.0.0 \
    --metrics-port="$BEACON_METRIC_PORT" \
    --listen-address=0.0.0.0 \
    --graffiti="lighthouse-minimal-$IP_ADDR" \
    --target-peers="$CONSENSUS_TARGET_PEERS" \
    --http-allow-sync-stalled \
    --merge \
    --disable-packet-filter \
    --execution-endpoints="http://$HTTP_WEB3_IP_ADDR:$EXECUTION_HTTP_PORT" \
    --eth1-endpoints="http://$HTTP_WEB3_IP_ADDR:$EXECUTION_HTTP_PORT" \
    --terminal-total-difficulty-override="$TERMINALTOTALDIFFICULTY" \
    --validator-monitor-auto \
    --suggested-fee-recipient="0x00000000219ab540356cbb839cbe05303d7705fa" \
    --enable-private-discovery \
    --subscribe-all-subnets &

sleep 10
lighthouse \
    --testnet-dir="$TESTNET_DIR" \
	vc \
    --validators-dir "$NODE_DIR/keys" \
    --secrets-dir "$NODE_DIR/secrets" \
	--init-slashing-protection \
    --server="http://127.0.0.1:$BEACON_API_PORT" \
    --graffiti="lighthouse-minimal-$IP_ADDR" \
    --http --http-port="$VALIDATOR_RPC_PORT" \
    --suggested-fee-recipient="0x00000000219ab540356cbb839cbe05303d7705fa" \
    --metrics --metrics-address=0.0.0.0 --metrics-port="$VALIDATOR_METRIC_PORT"
