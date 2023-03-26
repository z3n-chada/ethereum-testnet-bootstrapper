# git clone -b master https://github.com/MariusVanDerWijden/tx-fuzz


git clone -b main https://github.com/kurtosis-tech/tx-fuzz

cp tx-fuzzer.Dockerfile tx-fuzz/tx-fuzzer.Dockerfile

cd tx-fuzz && docker build --registries-conf=`pwd`/../../../../registries.conf --no-cache -t tx-fuzzer -f tx-fuzzer.Dockerfile .
# cd tx-fuzz && docker build -t tx-fuzzer -f tx-fuzzer.Dockerfile .
# docker build -t tx-fuzzer -f tx-fuzzer.Dockerfile .


cd ../

rm -rf tx-fuzz
