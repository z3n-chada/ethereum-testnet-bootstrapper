FROM etb-client-builder:latest as base

FROM base as builder

WORKDIR /git

ARG GIT_BRANCH="develop"

RUN mkdir -p /git/src/github.com/prysmaticlabs/
RUN mkdir -p /build

RUN cd /git/src/github.com/prysmaticlabs/ && \
    git clone --branch "$GIT_BRANCH" \
    --recurse-submodules \
    --depth 1 \
    https://github.com/prysmaticlabs/prysm

WORKDIR /git/src/github.com/prysmaticlabs/prysm
RUN git log -n 1 --format=format:"%H" > /prysm.version

#Antithesis Instrumentation

# add items to this exclusions list to exclude them from instrumentation
RUN touch /opt/antithesis/go_instrumentation/exclusions.txt
# Ignore files with special `// go:` comments due to this issue: https://trello.com/c/Wmaxylu9
RUN grep -l -r go: | grep \.go$ >> /opt/antithesis/go_instrumentation/exclusions.txt
RUN grep -l -r snappy | grep \.go$ >> /opt/antithesis/go_instrumentation/exclusions.txt

# Antithesis -------------------------------------------------
WORKDIR /git/src/github.com/prysmaticlabs
RUN mkdir -p prysm_instrumented && LD_LIBRARY_PATH=/opt/antithesis/go_instrumentation/lib /opt/antithesis/go_instrumentation/bin/goinstrumentor -antithesis=/opt/antithesis/go_instrumentation/instrumentation/go/wrappers/ -exclude=/opt/antithesis/go_instrumentation/exclusions.txt -stderrthreshold=INFO prysm prysm_instrumented
RUN cp -r prysm_instrumented/customer/* prysm/
RUN cd prysm && go mod edit -require=antithesis.com/instrumentation/wrappers@v1.0.0 -replace antithesis.com/instrumentation/wrappers=/opt/antithesis/go_instrumentation/instrumentation/go/wrappers
# Antithesis -------------------------------------------------
# Get dependencies
RUN cd /git/src/github.com/prysmaticlabs/prysm && go get -t -d ./...

#Build with instrumentation
RUN cd /git/src/github.com/prysmaticlabs/prysm && CGO_CFLAGS="-I/opt/antithesis/go_instrumentation/include" CGO_LDFLAGS="-L/opt/antithesis/go_instrumentation/lib" go build -o /build ./...
RUN go env GOPATH

FROM scratch

COPY --from=builder /build/beacon-chain /usr/local/bin/
COPY --from=builder /build/validator /usr/local/bin/
COPY --from=builder /build/client-stats /usr/local/bin/
COPY --from=builder /git/src/github.com/prysmaticlabs/prysm_instrumented/symbols/* /opt/antithesis/symbols/
COPY --from=builder /prysm.version /prysm.version
COPY --from=builder /git/src/github.com/prysmaticlabs/* /git/src/github.com/prysmaticlabs/

