#!/bin/bash

./build-tx-fuzzer.sh

BUILDKIT=1 docker build -t geth:bad-block-creator -f geth_bad-block-creator-inst.Dockerfile .
BUILDKIT=1 docker build -t prysm:evil-shapella -f prysm_evil-shapella.Dockerfile .
