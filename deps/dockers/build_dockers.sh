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
antithesis_log_step "Building base images"
build_image "etb-client-builder" "etb-client-builder.Dockerfile"
build_image "etb-client-runner" "etb-client-runner.Dockerfile"

cd ../el/ || exit 1
antithesis_log_step "Building geth"
build_image "geth:etb" "geth.Dockerfile"
antithesis_log_step "Building besu"
build_image "besu:etb" "besu.Dockerfile"
antithesis_log_step "Building nethermind"
build_image "nethermind:etb" "nethermind.Dockerfile"

cd ../cl/ || exit 1
./build_dockers.sh

cd ../fuzzers/ || exit 1
echo "<<<<<<<<<< ANTITHESIS >>>>>>>>>> - building fuzzers."
./build_dockers.sh

cd ../base-images/ || exit 1
antithesis_log_step "Building etb-all-clients"
build_image "etb-all-clients:minimal" "etb-all-clients_minimal.Dockerfile"
build_image "etb-all-clients:minimal-fuzz" "etb-all-clients_minimal-fuzz.Dockerfile"
build_image "etb-all-clients-inst:minimal" "etb-all-clients_minimal_inst.Dockerfile"