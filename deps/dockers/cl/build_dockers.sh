#!/bin/bash

BUILDKIT=1 docker build -t lighthouse:etb -f lighthouse.Dockerfile .
BUILDKIT=1 docker build -t lodestar:etb -f lodestar.Dockerfile .
BUILDKIT=1 docker build -t teku:etb -f teku.Dockerfile .
BUILDKIT=1 docker build -t nimbus:etb -f nimbus.Dockerfile .
BUILDKIT=1 docker build -t prysm:etb -f prysm.Dockerfile .

BUILDKIT=1 docker build -t nimbus:etb-minimal -f nimbus_minimal.Dockerfile .
BUILDKIT=1 docker build -t teku:etb-minimal -f teku_minimal.Dockerfile .
BUILDKIT=1 docker build -t lodestar:etb-minimal -f lodestar_minimal.Dockerfile .
BUILDKIT=1 docker build -t lighthouse:etb-minimal -f lighthouse_minimal.Dockerfile .