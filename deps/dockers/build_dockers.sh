# build the builder first
cd base-images/ || exit
# echo "Building base images."
BUILDKIT=1 docker build --registries-conf=`pwd`/../../../registries.conf -t etb-client-builder -f etb-client-builder.Dockerfile .
BUILDKIT=1 docker build --registries-conf=`pwd`/../../../registries.conf -t etb-client-runner -f etb-client-runner.Dockerfile .

# ## els then cls
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
# currently mainnet configs have not been modified to support the new boostrapper
BUILDKIT=1 docker build --registries-conf=`pwd`/../../../registries.conf --no-cache -t etb-all-clients:minimal -f etb-all-clients_minimal.Dockerfile .
BUILDKIT=1 docker build --registries-conf=`pwd`/../../../registries.conf --no-cache -t etb-all-clients:minimal-fuzz -f etb-all-clients_minimal-fuzz.Dockerfile .