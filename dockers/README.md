# Overview
This folder contains some non-size-optimized example docker images to build consensus and execution layer clients. You can easily modify source, rebuild, and then deploy them in a local testnet.

The directories are setup as follows:
1. kilnv2 cooresponds to client branches for bellatrix kilnv2 clients.
    - These are required for mainnet builds
2. base refers to platform independent versions of dockers 
    - Currently this is only consensus level bootnodes of which only one is currenly implemented.
3. fuzzers refers to fuzzer builds that can be inserted into the network. 
    - Configs that include -fuzz in the name require these fuzzers to be built.

In each of the folders you will find a build\_dockers.sh script that will build and tag all the Dockerfiles in that dir with the naming convention used in the config files.

Additionally each src/ dir cooresponds to a dir that allows you to change the source of a client before building for debugging purposes (this hasn't been finalized yet)
