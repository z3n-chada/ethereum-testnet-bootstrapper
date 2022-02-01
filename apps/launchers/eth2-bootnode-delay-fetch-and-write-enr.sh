#!/bin/bash

TO_FETCH=$1
TO_WRITE=$2

printf "waiting for bootnode api to come up."
until $(curl --output /dev/null --silent --head --fail $TO_FETCH); do
    printf "."
    sleep 1
done
curl "$1" > $2
