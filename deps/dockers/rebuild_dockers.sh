
### build the builder first
cd base-images/ || exit
echo "Building base images."
docker build --registries-conf=`pwd`/../../../registries.conf --no-cache -t etb-client-builder -f etb-client-builder.Dockerfile .
docker build --registries-conf=`pwd`/../../../registries.conf --no-cache -t etb-client-runner -f etb-client-runner.Dockerfile .

### els then cls
cd ../el/ || exit
echo "Building execution clients"
./rebuild_dockers.sh

cd ../cl/ || exit
# cd cl/ || exit
echo "Building consensus clients"
./rebuild_dockers.sh

cd ../fuzzers/ || exit
cd fuzzers/ || exit
echo "building fuzzers."
./rebuild_dockers.sh
#
cd ../base-images/ || exit
# cd base-images/ || exit
echo "Merging all clients."
# currently mainnet configs have not been modified to support the new boostrapper
docker build --registries-conf=`pwd`/../../../registries.conf --no-cache -t etb-all-clients:minimal -f etb-all-clients_minimal.Dockerfile .
docker build --registries-conf=`pwd`/../../../registries.conf --no-cache -t etb-all-clients:minimal-fuzz -f etb-all-clients_minimal-fuzz.Dockerfile .