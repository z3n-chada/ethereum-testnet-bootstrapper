FROM etb-client-builder as builder

RUN mkdir -p /go/src/github.com/ethereum/
WORKDIR /go/src/github.com/ethereum/

# RUN git clone https://github.com/edwards-antithesis/go-ethereum \
RUN git clone https://github.com/MariusVanDerWijden/go-ethereum.git \
    && cd go-ethereum \
    && git checkout bad-block-generator

# Get dependencies
RUN cd /go/src/github.com/ethereum/go-ethereum && go get -t -d ./...

RUN cd go-ethereum \
    && go install ./...

RUN cd go-ethereum && git log -n 1 --format=format:"%H" > /geth.version

FROM scratch

COPY --from=builder /root/go/bin/geth /usr/local/bin/geth
COPY --from=builder /root/go/bin/bootnode /usr/local/bin/bootnode
COPY --from=builder /go/src/github.com/ethereum/geth_instrumented/symbols/* /opt/antithesis/symbols/
COPY --from=builder /geth.version /geth.version

ENTRYPOINT ["/bin/bash"]
