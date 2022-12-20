#!/bin/bash

# build the builder first
cd base-images/ || exit
BUILDKIT=1 docker build --no-cache -t etb-client-builder -f etb-client-builder.Dockerfile .
BUILDKIT=1 docker build --no-cache -t etb-client-runner -f etb-client-runner.Dockerfile .

## els then cls
cd ../el/ || exit
for df in $(ls | grep Dockerfile); do
    echo $df
    i=$(echo $df | tr '_' ':')
    image=$(echo "${i::-11}")
    BUILDKIT=1 docker build --no-cache -f "$df" -t "$image" .
    done

cd ../cl/ || exit
for df in $(ls | grep Dockerfile); do
    echo $df
    i=`echo $df | tr '_' ':'`
    image=`echo "${i::-11}"`
    BUILDKIT=1 docker build --no-cache -f "$df" -t "$image" .
    done

#
cd ../fuzzers/ || exit
./build_dockers.sh

cd ../base_images/ || exit
BUILDKIT=1 docker build --no-cache -t etb-all-clients:lastest -f etb-all-clients.Dockerfile .
