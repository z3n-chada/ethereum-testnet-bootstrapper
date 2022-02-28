#!/bin/bash -e

echo "launching bootstrapper"

mkdir -p /data/local_testnet

python3 /source/apps/bootstrap_simulation.py "$@"
