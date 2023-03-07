#!/bin/bash

BUILDKIT=1 docker build --no-cache -t geth:etb -f geth.Dockerfile .
BUILDKIT=1 docker build --no-cache -t besu:etb -f besu.Dockerfile .
BUILDKIT=1 docker build --no-cache -t nethermind:etb -f nethermind.Dockerfile .
