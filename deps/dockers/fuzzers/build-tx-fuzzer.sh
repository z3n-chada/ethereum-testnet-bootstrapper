

git clone -b main https://github.com/kurtosis-tech/tx-fuzz

cp tx-fuzzer.Dockerfile tx-fuzz/tx-fuzzer.Dockerfile

# cd tx-fuzz && docker build --no-cache -t tx-fuzzer -f tx-fuzzer.Dockerfile .
cd tx-fuzz && docker build -t tx-fuzzer -f tx-fuzzer.Dockerfile .

cd ../

rm -rf tx-fuzz
