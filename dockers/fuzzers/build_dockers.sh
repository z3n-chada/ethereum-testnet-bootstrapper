#!/bin/bash

./build-tx-fuzzer.sh

docker build -t geth-bad-block:merge-kiln-bad-block -f geth-bad-block_merge-kiln-bad-block.Dockerfile .

docker build -t nimbus-bad-block-fuzz:kilnv2 -f nimbus-fuzz_kilnv2.Dockerfile .
docker build -t lighthouse-bad-block-fuzz:kilnv2 -f lighthouse-fuzz_kilnv2.Dockerfile .
docker build -t prysm-bad-block-fuzz:kilnv2 -f prysm-fuzz_kilnv2.Dockerfile .
docker build -t lodestar-bad-block-fuzz:kilnv2 -f lodestar-fuzz_kilnv2.Dockerfile .
docker build -t teku-bad-block-fuzz:kilnv2 -f teku-fuzz_kilnv2.Dockerfile .

