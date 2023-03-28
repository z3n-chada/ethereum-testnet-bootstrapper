FROM etb-client-builder:latest as rocks_builder

WORKDIR /git/rocksdb

RUN make clean && make -j2 shared_lib
RUN mkdir -p /rocksdb/lib && cp librocksdb.so* /rocksdb/lib/


FROM golang:1.18 as go_builder

RUN go install github.com/wealdtech/ethereal/v2@latest \
    && go install github.com/wealdtech/ethdo@latest \
    && go install github.com/protolambda/eth2-val-tools@latest


FROM debian:bullseye-slim

WORKDIR /git

RUN apt update && apt install curl ca-certificates -y --no-install-recommends \
    wget \
    lsb-release \
    software-properties-common && \
    curl -sL https://deb.nodesource.com/setup_18.x | bash -

RUN wget https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    rm packages-microsoft-prod.deb

RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    libgflags-dev \
    libsnappy-dev \
    zlib1g-dev \
    libbz2-dev \
    liblz4-dev \
    libzstd-dev \
    openjdk-17-jre \
    dotnet-runtime-7.0 \
    aspnetcore-runtime-7.0 \
    python3-dev \
    python3-pip

RUN pip3 install ruamel.yaml web3

COPY --from=rocks_builder /rocksdb/lib/ /usr/local/rocksdb/lib/
# Antithesis instrumentation resources
COPY --from=rocks_builder /usr/lib/libvoidstar.so /usr/lib/libvoidstar.so

RUN cp /usr/local/rocksdb/lib/librocksdb.so* /usr/lib

# for coverage artifacts and runtime libraries.
RUN wget --no-check-certificate https://apt.llvm.org/llvm.sh && \
    chmod +x llvm.sh && \
    ./llvm.sh 14

COPY --from=go_builder /go/bin/ethereal /usr/local/bin/ethereal
COPY --from=go_builder /go/bin/ethdo /usr/local/bin/ethdo
COPY --from=go_builder /go/bin/eth2-val-tools /usr/local/bin/eth2-val-tools

ENV LLVM_CONFIG=llvm-config-14

ENTRYPOINT ["/bin/bash"]
