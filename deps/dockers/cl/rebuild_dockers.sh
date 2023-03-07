#!/bin/bash

BUILDKIT=1 docker build --no-cache -t lighthouse:etb -f lighthouse.Dockerfile .
BUILDKIT=1 docker build --no-cache -t lodestar:etb -f lodestar.Dockerfile .
BUILDKIT=1 docker build --no-cache -t teku:etb -f teku.Dockerfile .
BUILDKIT=1 docker build --no-cache -t nimbus:etb -f nimbus.Dockerfile .
BUILDKIT=1 docker build --no-cache -t prysm:etb -f prysm.Dockerfile .

BUILDKIT=1 docker build --no-cache -t nimbus:etb-minimal -f nimbus_minimal.Dockerfile .
BUILDKIT=1 docker build --no-cache -t teku:etb-minimal -f teku_minimal.Dockerfile .
BUILDKIT=1 docker build --no-cache -t lodestar:etb-minimal -f lodestar_minimal.Dockerfile .
BUILDKIT=1 docker build --no-cache -t lighthouse:etb-minimal -f lighthouse_minimal.Dockerfile .
BUILDKIT=1 docker build --no-cache -t prysm:etb-minimal -f prysm_minimal.Dockerfile .
