FROM golang:1.17 as geth_builder
RUN git clone https://github.com/MariusVanDerWijden/go-ethereum.git \
    && cd go-ethereum && git checkout merge-kiln-v2 \
    && make geth

FROM rust:1.56.1-bullseye AS builder
WORKDIR /git
RUN apt-get update && apt-get -y upgrade && apt-get install -y cmake libclang-dev
RUN git clone https://github.com/sigp/lighthouse.git && cd lighthouse && git checkout unstable
RUN cd lighthouse && make 

from debian:latest

COPY --from=builder /usr/local/cargo/bin/lighthouse /usr/local/bin/lighthouse
COPY --from=geth_builder /go/go-ethereum/build/bin/geth /usr/local/bin/geth
