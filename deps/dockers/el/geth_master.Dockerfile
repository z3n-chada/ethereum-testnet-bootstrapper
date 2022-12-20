FROM etb-client-builder:latest as base

from base as builder

RUN mkdir -p /go/src/github.com/ethereum/ 
WORKDIR /go/src/github.com/ethereum/

ARG GETH_BRANCH="master"

RUN git clone https://github.com/ethereum/go-ethereum \
    && cd go-ethereum \
    && git checkout ${GETH_BRANCH} 

# add items to this exclusions list to exclude them from instrumentation
RUN touch /opt/antithesis/go_instrumentation/exclusions.txt


# Antithesis -------------------------------------------------
WORKDIR /go/src/github.com/ethereum/
RUN mkdir -p geth_instrumented && LD_LIBRARY_PATH=/opt/antithesis/go_instrumentation/lib /opt/antithesis/go_instrumentation/bin/goinstrumentor -antithesis=/opt/antithesis/go_instrumentation/instrumentation/go/wrappers/ -exclude=/opt/antithesis/go_instrumentation/exclusions.txt -stderrthreshold=INFO go-ethereum geth_instrumented
RUN cp -r geth_instrumented/customer/* go-ethereum/
RUN cd go-ethereum && go mod edit -require=antithesis.com/instrumentation/wrappers@v1.0.0 -replace antithesis.com/instrumentation/wrappers=/opt/antithesis/go_instrumentation/instrumentation/go/wrappers 
# Antithesis -------------------------------------------------
# Get dependencies
RUN cd /go/src/github.com/ethereum/go-ethereum && go get -t -d ./...

RUN cd go-ethereum \
    && CGO_CFLAGS="-I/opt/antithesis/go_instrumentation/include" CGO_LDFLAGS="-L/opt/antithesis/go_instrumentation/lib" go install ./...

RUN cd go-ethereum && git log -n 1 --format=format:"%H" > /geth.version

FROM etb-client-runner

COPY --from=builder /root/go/bin/geth /usr/local/bin/geth
COPY --from=builder /root/go/bin/bootnode /usr/local/bin/bootnode
COPY --from=builder /go/src/github.com/ethereum/geth_instrumented/symbols/* /opt/antithesis/symbols/
COPY --from=builder /geth.version /geth.version


ENTRYPOINT ["/bin/bash"]
