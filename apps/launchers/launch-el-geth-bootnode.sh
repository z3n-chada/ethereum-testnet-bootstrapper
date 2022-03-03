#!/bin/bash

BOOTNODE_DATADIR=$1
IP_ADDR=$2
PORT=$3

mkdir -p $BOOTNODE_DATADIR

geth-bootnode -genkey "$BOOTNODE_DATADIR/bootnode.key" # create the node key

geth \
    --nodekey "$BOOTNODE_DATADIR/bootnode.key" \
    --datadir $BOOTNODE_DATADIR \
    --v5disc \
    --port $PORT \
    --nat "extip:$IP_ADDR" \
    --nodiscover &

while [ ! -f "$BOOTNODE_DATADIR/geth.ipc" ]; do
    sleep 1
    echo "Bootnode waiting for IPC connection ($BOOTNODE_DATADIR/geth.ipc)"
done

ENODE=`python3 /source/apps/get_geth_enr.py --geth-ipc "$BOOTNODE_DATADIR/geth.ipc"`
echo $ENODE
