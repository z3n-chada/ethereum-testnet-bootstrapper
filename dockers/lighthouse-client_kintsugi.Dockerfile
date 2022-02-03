FROM rust:1.56.1-bullseye AS builder
WORKDIR /git
RUN apt-get update && apt-get -y upgrade && apt-get install -y cmake libclang-dev
RUN git clone https://github.com/sigp/lighthouse.git && cd lighthouse && git checkout stable
RUN cd lighthouse && make 

from debian:latest

COPY --from=builder /usr/local/cargo/bin/lighthouse /usr/local/bin/lighthouse
