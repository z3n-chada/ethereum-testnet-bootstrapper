#!/bin/bash

BUILDKIT=1 docker build -t geth:etb -f geth.Dockerfile .
BUILDKIT=1 docker build -t besu:etb -f besu.Dockerfile .
BUILDKIT=1 docker build -t nethermind:etb -f nethermind.Dockerfile .

BUILDKIT=1 docker build -t geth:capella -f geth_capella.Dockerfile .
BUILDKIT=1 docker build -t besu:capella -f besu_capella.Dockerfile .
BUILDKIT=1 docker build -t nethermind:capella -f nethermind_capella.Dockerfile .
