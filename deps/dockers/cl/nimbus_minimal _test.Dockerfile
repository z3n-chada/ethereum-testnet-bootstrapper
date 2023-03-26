FROM etb-client-builder:latest as builder

WORKDIR /git
# Included here to avoid build-time complaints
ARG BRANCH="unstable"

RUN git clone https://github.com/status-im/nimbus-eth2.git && cd nimbus-eth2 && git checkout unstable
# RUN git clone https://github.com/status-im/nimbus-eth2.git && cd nimbus-eth2 && git checkout v23.3.2


#RUN cd nimbus-eth2 && git fetch origin pull/4519/head:pull_4519 && git checkout pull_4519

RUN cd nimbus-eth2 && make -j64 update

# RUN cd nimbus-eth2 && make -j64 nimbus_beacon_node NIMFLAGS="-d:const_preset=minimal -d:disableMarchNative --cc:clang --clang.exe:clang-15 --clang.linkerexe:clang-15 --passC:'-fno-lto -fsanitize-coverage=trace-pc-guard' --passL:'-fno-lto -L/usr/lib/ -lvoidstar'"
RUN cd nimbus-eth2 && make local-testnet-minimal

# RUN cd nimbus-eth2 \
#     && git log -n 1 --format=format:"%H" > /nimbus.version

# FROM scratch

# COPY --from=builder /git/nimbus-eth2/build/nimbus_beacon_node /usr/local/bin/nimbus_beacon_node
# COPY --from=builder /nimbus.version /nimbus.version