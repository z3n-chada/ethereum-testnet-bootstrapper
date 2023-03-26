

./build-tx-fuzzer.sh

BUILDKIT=1 docker build --registries-conf=`pwd`/../../../registries.conf -t lighthouse:etb-minimal-fuzz -f lighthouse-fuzz_minimal.Dockerfile .
BUILDKIT=1 docker build --registries-conf=`pwd`/../../../registries.conf -t prysm:etb-minimal-fuzz -f prysm-fuzz_minimal.Dockerfile .
BUILDKIT=1 docker build --registries-conf=`pwd`/../../../registries.conf -t geth:bad-block-creator -f geth_bad-block-creator-inst.Dockerfile .
BUILDKIT=1 docker build --registries-conf=`pwd`/../../../registries.conf -t prysm:evil-shapella -f prysm_evil-shapella.Dockerfile .