#!/bin/bash

env_vars=(
  "IP_ADDRESS"
  "CONSENSUS_BOOTNODE_API_PORT"
  "CONSENSUS_BOOTNODE_PRIVATE_KEY"
  "CONSENSUS_BOOTNODE_ENR_FILE"
  "CONSENSUS_BOOTNODE_ENR_PORT"
  "CONSENSUS_BOOTNODE_CHECKPOINT_FILE"
)

# verify vars we need are set and available.
for var in "${env_vars[@]}" ; do
    if [[ -z "${!var}" ]]; then
        echo "Eth2-bootnode error in geth var check."
        echo "$var not set"
        exit 1
    fi
done

# wait for the bootnode checkpoint file before starting.
while [ ! -f "$CONSENSUS_BOOTNODE_CHECKPOINT_FILE" ]; do
  echo "eth2-bootnode waiting for bootnode checkpoint file."
    sleep 1
done

# the clients expect a static bootnode file to come online. so we launch the
# bootnode and then fetch the file and write it ourselves.

# interact with the bootnode and write the enr to disk.
write_enr_file () {
  enr_fetch_address="$IP_ADDRESS:$CONSENSUS_BOOTNODE_API_PORT/enr"
  until $(curl --output /dev/null --silent --head --fail $enr_fetch_address); do
    echo "waiting on bootnode to come up to write... ($enr_fetch_address)"
    sleep 1
  done
  echo "eth2-bootnode: writing enr to file ($CONSENSUS_BOOTNODE_ENR_FILE)"
  curl "$enr_fetch_address" > $CONSENSUS_BOOTNODE_ENR_FILE
}

write_enr_file &

echo "launching eth2-bootnode"

eth2-bootnode \
    --priv "$CONSENSUS_BOOTNODE_PRIVATE_KEY" \
    --enr-ip "$IP_ADDRESS" \
    --enr-udp "$CONSENSUS_BOOTNODE_ENR_PORT" \
    --listen-ip 0.0.0.0 \
    --listen-udp "$CONSENSUS_BOOTNODE_ENR_PORT" \
    --api-addr "0.0.0.0:$CONSENSUS_BOOTNODE_API_PORT"
