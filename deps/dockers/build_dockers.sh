#!/bin/bash

# build the builder first
cd base-images/ || exit
echo "Building base images."
BUILDKIT=1 docker build -t etb-client-builder -f etb-client-builder.Dockerfile .
BUILDKIT=1 docker build -t etb-client-runner -f etb-client-runner.Dockerfile .

### els then cls
cd ../el/ || exit
echo "Building execution clients"
./build_dockers.sh

cd ../cl/ || exit
echo "Building consensus clients"
./build_dockers.sh

cd ../fuzzers/ || exit
echo "building fuzzers."
./build_dockers.sh
#
cd ../base-images/ || exit
echo "Merging all clients."
BUILDKIT=1 docker build --no-cache -t etb-all-clients:lastest -f etb-all-clients.Dockerfile .
