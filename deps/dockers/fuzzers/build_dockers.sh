#!/bin/bash

./build-tx-fuzzer.sh

BUILDKIT=1 docker build -t lighthouse:etb-minimal-fuzz -f lighthouse-fuzz_minimal.Dockerfile .
BUILDKIT=1 docker build -t prysm:etb-minimal-fuzz -f prysm-fuzz_minimal.Dockerfile .