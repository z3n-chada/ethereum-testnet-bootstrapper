FROM golang:1.17 as geth_builder
RUN git clone https://github.com/MariusVanDerWijden/go-ethereum.git \
    && cd go-ethereum && git checkout merge-kiln-bad-block \
    && make geth

from debian:latest

RUN apt-get update && apt-get install -y git openjdk-11-jdk && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /git
RUN git clone https://github.com/Consensys/teku.git && \
    cd /git/teku && git checkout master && \
    ./gradlew distTar installDist


RUN ln -s /git/teku/build/install/teku/bin/teku /usr/local/bin/teku

COPY --from=geth_builder /go/go-ethereum/build/bin/geth /usr/local/bin/geth

ENTRYPOINT ["/bin/bash"]
