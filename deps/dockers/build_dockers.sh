#!/usr/bin/env bash

# We'll store the list of failed images in this log file
export FAILED_IMAGES_LOG=`pwd`/failed_images.log
# Clear the log file's contents (or create if does not already exist)
echo -n > $FAILED_IMAGES_LOG
# Import `build_image` and `antithesis_log_step` functions
source ./common.sh

# EL, CL and Fuzzer images depend on the etb-client-builder image
# The etb-all-clients images depend on the etb-client-runner image
cd base-images/ || exit 1
antithesis_log_step "Building base images (using cache)"
build_image "etb-client-builder:latest" "etb-client-builder.Dockerfile"
build_image "etb-client-runner:latest" "etb-client-runner.Dockerfile"

cd ../el/ || exit 1
antithesis_log_step "Building geth"
build_image "geth:etb" "geth.Dockerfile"
antithesis_log_step "Building besu"
build_image "besu:etb" "besu.Dockerfile"
antithesis_log_step "Building nethermind"
build_image "nethermind:etb" "nethermind.Dockerfile"

cd ../cl/ || exit 1
antithesis_log_step "Building nimbus"
build_image "nimbus:etb-minimal" "nimbus_minimal.Dockerfile"
antithesis_log_step "Building teku"
build_image "teku:etb-minimal" "teku_minimal.Dockerfile"
antithesis_log_step "Building lodestar"
build_image "lodestar:etb-minimal" "lodestar_minimal.Dockerfile"
antithesis_log_step "Building lighthouse"
build_image "lighthouse:etb-minimal" "lighthouse_minimal.Dockerfile"
antithesis_log_step "Building prysm"
build_image "prysm:etb-minimal" "prysm_minimal.Dockerfile"

cd ../fuzzers/ || exit 1
antithesis_log_step "Building tx-fuzzer"
build_image "tx-fuzzer" "tx-fuzzer.Dockerfile"
antithesis_log_step "Building lighthouse-fuzz"
build_image "lighthouse:etb-minimal-fuzz" "lighthouse-fuzz_minimal.Dockerfile"
antithesis_log_step "Building prysm-fuzz"
build_image "prysm:etb-minimal-fuzz" "prysm-fuzz_minimal.Dockerfile"
antithesis_log_step "Building geth-bad-block-creator"
build_image "geth:bad-block-creator" "geth_bad-block-creator.Dockerfile"

cd ../base-images/ || exit 1
antithesis_log_step "Building etb-all-clients"
build_image "etb-all-clients:minimal" "etb-all-clients_minimal.Dockerfile"
build_image "etb-all-clients:minimal-fuzz" "etb-all-clients_minimal-fuzz.Dockerfile"
build_image "etb-all-clients-inst:minimal" "etb-all-clients_minimal_inst.Dockerfile"

# Check if failed images log contains entries
if [ -s $FAILED_IMAGES_LOG ]; then
    printf "\n\n"
    RED='\033[0;31m'
    NO_COLOR='\033[0m'
    printf "${RED}The following images failed to build:${NO_COLOR}\n"
    cat $FAILED_IMAGES_LOG
    printf "\n\n"
else
    rm $FAILED_IMAGES_LOG

    echo "Images successfully built. Remember to push to the registry."
fi
