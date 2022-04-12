#!/bin/bash

TO_FETCH=$1
TO_WRITE=$2

echo "waiting for bootnode api to come up."
until $(curl --output /dev/null --silent --head --fail $TO_FETCH); do
    echo "waiting on bootnode to come up to write... ($TO_FETCH)"
    sleep 1
done
echo "writing $TO_FETCH to $TO_WRITE"
curl "$1" > $2
