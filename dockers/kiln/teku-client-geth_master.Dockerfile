FROM golang:1.17 as builder
RUN git clone https://github.com/MariusVanDerWijden/go-ethereum.git \
    && cd go-ethereum && git checkout merge-kiln \
    && make geth

FROM debian:latest

WORKDIR /git

RUN apt-get update && apt-get install -y git openjdk-11-jdk && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/Consensys/teku.git && \
    cd /git/teku && git checkout master && \
    ./gradlew distTar installDist


RUN ln -s /git/teku/build/install/teku/bin/teku /usr/local/bin/teku
COPY --from=builder /go/go-ethereum/build/bin/geth /usr/local/bin/geth

ENTRYPOINT ["/bin/bash"]

# not very minimal but unsure how to move all dependencies for java to use builder copy 
