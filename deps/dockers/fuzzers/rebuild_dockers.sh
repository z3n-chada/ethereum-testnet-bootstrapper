#!/bin/bash

./build-tx-fuzzer.sh

BUILDKIT=1 docker build --no-cache -t lighthouse:etb-minimal-fuzz -f lighthouse-fuzz_minimal.Dockerfile .
BUILDKIT=1 docker build --no-cache -t prysm:etb-minimal-fuzz -f prysm-fuzz_minimal.Dockerfile .
