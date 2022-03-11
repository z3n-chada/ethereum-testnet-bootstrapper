FROM golang:1.17 as geth_builder
RUN git clone https://github.com/MariusVanDerWijden/go-ethereum.git \
    && cd go-ethereum && git checkout merge-kiln-v2 \
    && make geth

FROM node:16-bullseye

WORKDIR /usr/app

ARG VERSION=next
ENV VERSION=$VERSION
RUN npm install -g npm@8.5.4
RUN npm install @chainsafe/lodestar-cli@$VERSION

RUN apt update; apt install -y g++ build-essential python3 python3-dev nodejs

COPY --from=geth_builder /go/go-ethereum/build/bin/geth /usr/local/bin/geth

RUN ln -s /usr/app/node_modules/.bin/lodestar /usr/local/bin/lodestar

ENTRYPOINT ["/bin/bash"]

