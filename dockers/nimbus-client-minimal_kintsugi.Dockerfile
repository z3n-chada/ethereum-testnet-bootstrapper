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

RUN git clone --recurse-submodules -b kintsugi https://github.com/status-im/nimbus-eth2.git

WORKDIR /git/nimbus-eth2

RUN make update

RUN make -j64 nimbus_beacon_node NIMFLAGS="--cc:clang --clang.exe:clang-13 --clang.linkerexe:clang-13 -d:const_preset=minimal -d:SECONDS_PER_SLOT=12"

RUN make -j64 nimbus_validator_client NIMFLAGS="--cc:clang --clang.exe:clang-13 --clang.linkerexe:clang-13 -d:const_preset=minimal -d:SECONDS_PER_SLOT=12"

FROM debian:latest

COPY --from=builder /git/nimbus-eth2/build/nimbus_beacon_node /usr/local/bin/nimbus_beacon_node
COPY --from=builder /git/nimbus-eth2/build/nimbus_validator_client /usr/local/bin/nimbus_validator_client

ENTRYPOINT ["/bin/bash"]
