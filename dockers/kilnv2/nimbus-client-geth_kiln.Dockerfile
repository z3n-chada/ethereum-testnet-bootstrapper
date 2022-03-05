FROM golang:1.17 as geth_builder
RUN git clone https://github.com/MariusVanDerWijden/go-ethereum.git \
    && cd go-ethereum && git checkout merge-kiln-v2 \
    && make geth

FROM ubuntu:18.04 as builder
# Update ubuntu
RUN apt-get update && \
	apt-get install -y --no-install-recommends \
		git \
        wget \
        build-essential \
        lsb-release wget software-properties-common \
        gpg-agent \
        nim

WORKDIR /git

RUN wget --no-check-certificate https://apt.llvm.org/llvm.sh && chmod +x llvm.sh && ./llvm.sh 13

ENV LLVM_CONFIG=llvm-config-13

RUN git clone https://github.com/status-im/nimbus-eth2.git

RUN cd nimbus-eth2 && git checkout V5X 


WORKDIR /git/nimbus-eth2

RUN make -j64 nimbus_beacon_node NIMFLAGS="--cc:clang --clang.exe:clang-13 --clang.linkerexe:clang-13"

RUN make -j64 nimbus_validator_client NIMFLAGS="--cc:clang --clang.exe:clang-13 --clang.linkerexe:clang-13"

FROM debian:latest

COPY --from=builder /git/nimbus-eth2/build/nimbus_beacon_node /usr/local/bin/nimbus_beacon_node
COPY --from=builder /git/nimbus-eth2/build/nimbus_validator_client /usr/local/bin/nimbus_validator_client
COPY --from=geth_builder /go/go-ethereum/build/bin/geth /usr/local/bin/geth

ENTRYPOINT ["/bin/bash"]
