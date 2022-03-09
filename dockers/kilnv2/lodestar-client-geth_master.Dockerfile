FROM golang:1.17 as geth_builder
RUN git clone https://github.com/MariusVanDerWijden/go-ethereum.git \
    && cd go-ethereum && git checkout merge-kiln-v2 \
    && make geth

FROM ubuntu:18.04

# Update ubuntu
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        software-properties-common \
        curl \
        gpg-agent \
        git \
        build-essential \
        make \
        gcc


# Install nodejs
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash

# Install npm & nodejs
RUN apt-get update && \
    apt-get install -y \
    nodejs

WORKDIR /git

# Install lodestar
RUN npm i @chainsafe/lodestar-beacon-state-transition
RUN npm i @chainsafe/lodestar-types
RUN npm i @chainsafe/lodestar-config
RUN npm i @chainsafe/discv5

COPY --from=geth_builder /go/go-ethereum/build/bin/geth /usr/local/bin/geth

ENTRYPOINT ["/bin/bash"]
