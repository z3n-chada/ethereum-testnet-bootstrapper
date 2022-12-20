#!/bin/bash

for df in $(ls | grep Dockerfile); do
    echo $df
    i=`echo $df | tr '_' ':'`
    image=`echo "${i::-11}"`
    BUILDKIT=1 docker build --no-cache -f "$df" -t "$image" .
done


