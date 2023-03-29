FROM etb-client-builder:latest as builder

ARG BRANCH="master"

RUN mkdir -p /go/src/github.com/ethereum/
WORKDIR /go/src/github.com/ethereum/

RUN git clone --depth=1 --branch="${BRANCH}" https://github.com/ethereum/go-ethereum.git && \
    cd go-ethereum && \
    git log -n 1 --format=format:"%H" > /geth.version

RUN mkdir geth_instrumented
RUN /opt/antithesis/go_instrumentation/bin/goinstrumentor \
    -logtostderr -stderrthreshold=INFO \
    -antithesis /opt/antithesis/go_instrumentation/instrumentation/go/wrappers \
    go-ethereum geth_instrumented

WORKDIR /go/src/github.com/ethereum/go-ethereum
RUN go get -t -d ./...
RUN go install ./... && \
    mv /root/go/bin/geth /tmp/geth_uninstrumented && \
    mv /root/go/bin/bootnode /tmp/bootnode_uninstrumented

WORKDIR /go/src/github.com/ethereum/geth_instrumented/customer
RUN go get -t -d ./...
RUN go install -race ./... && mv /root/go/bin/geth /tmp/geth_race
RUN go install ./...


FROM scratch

COPY --from=builder /root/go/bin/geth /usr/local/bin/geth
COPY --from=builder /root/go/bin/bootnode /usr/local/bin/bootnode
COPY --from=builder /tmp/geth_race /usr/local/bin/geth_race
COPY --from=builder /tmp/geth_uninstrumented /usr/local/bin/geth_uninstrumented
COPY --from=builder /tmp/bootnode_uninstrumented /usr/local/bin/bootnode_uninstrumented
COPY --from=builder /go/src/github.com/ethereum/geth_instrumented/symbols/* /opt/antithesis/symbols/
COPY --from=builder /go/src/github.com/ethereum/geth_instrumented/customer /geth_instrumented_code
COPY --from=builder /geth.version /geth.version