FROM golang:1.17 as geth_builder
RUN git clone https://github.com/MariusVanDerWijden/go-ethereum.git \
    && cd go-ethereum && git checkout merge-kiln-bad-block \
    && make geth

from debian:latest

COPY --from=geth_builder /go/go-ethereum/build/bin/geth /usr/local/bin/geth
