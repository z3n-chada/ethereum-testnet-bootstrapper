#!/bin/bash

for df in $(ls | grep Dockerfile); do
    echo $df
    i=`echo $df | tr '_' ':'`
    image="${i::-11}"
    BUILDKIT=1 docker build -f "$df" -t "${i::-11}" .
done

