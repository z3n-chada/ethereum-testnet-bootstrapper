FROM etb-client-builder:latest as builder

ARG BRANCH="unstable"

WORKDIR /git

RUN git clone --depth=1 --branch="${BRANCH}" https://github.com/status-im/nimbus-eth2.git

WORKDIR /git/nimbus-eth2

RUN git log -n 1 --format=format:"%H" > /nimbus.version
RUN make -j4 update
RUN make -j4 nimbus_beacon_node NIMFLAGS="-d:const_preset=minimal -d:web3_consensus_const_preset=minimal -d:disableMarchNative --cc:clang --clang.exe:clang-15 --clang.linkerexe:clang-15"
RUN mv /git/nimbus-eth2/build/nimbus_beacon_node /tmp/nimbus_beacon_node_uninstrumented
RUN make clean
RUN make -j4 USE_LIBBACKTRACE=0 nimbus_beacon_node NIMFLAGS="-d:const_preset=minimal -d:web3_consensus_const_preset=minimal -d:disableMarchNative --cc:clang --clang.exe:clang-15 --clang.linkerexe:clang-15 --passC:'-fno-lto -fsanitize-coverage=trace-pc-guard' --passL:'-fno-lto -L/usr/lib/ -lvoidstar'"


FROM scratch

COPY --from=builder /tmp/nimbus_beacon_node_uninstrumented /usr/local/bin/nimbus_beacon_node_uninstrumented
COPY --from=builder /git/nimbus-eth2/build/nimbus_beacon_node /usr/local/bin/nimbus_beacon_node
COPY --from=builder /nimbus.version /nimbus.version