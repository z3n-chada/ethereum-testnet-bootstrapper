FROM gcr.io/prysmaticlabs/build-agent AS builder

WORKDIR /git

RUN git clone --branch v4.0.0-rc.2 \
    --recurse-submodules \
    --depth 1 \
    https://github.com/prysmaticlabs/prysm

WORKDIR /git/prysm

RUN git log -n 1 --format=format:"%H" > /prysm.version

RUN echo "export MY_BAZEL_BIN=$(bazel info bazel-bin)" >> /envfile
RUN . /envfile; echo $MY_BAZEL_BIN
RUN sed -i 's/(bazel info bazel-bin)/MY_BAZEL_BIN/' ./hack/update-go-pbs.sh 
RUN sed -i 's/(bazel info bazel-bin)/MY_BAZEL_BIN/' ./hack/update-go-ssz.sh 
# Run with || true to ignore command issues with missing gofmt or missing goimports
RUN . /envfile; ./hack/update-go-pbs.sh --config=minimal || true
RUN . /envfile; ./hack/update-go-ssz.sh --config=minimal || true


# FROM golang:1.20.1-bullseye AS instrumentor
FROM etb-client-builder:latest as instrumentor

COPY --from=builder /git/prysm /git/prysm
WORKDIR /git

RUN mkdir -p /opt/antithesis/
RUN mkdir -p prysm_instrumented
RUN /opt/antithesis/go_instrumentation/bin/goinstrumentor -version
RUN /opt/antithesis/go_instrumentation/bin/goinstrumentor \
    -logtostderr -stderrthreshold=INFO \
    -antithesis /opt/antithesis/go_instrumentation/instrumentation/go/wrappers \
    prysm prysm_instrumented

WORKDIR /git/prysm_instrumented/customer
RUN go build -tags minimal -o /validator ./cmd/validator
RUN go build -tags minimal -o /beacon-chain ./cmd/beacon-chain

RUN /validator --version
RUN /beacon-chain --version

FROM scratch

COPY --from=instrumentor /beacon-chain /usr/local/bin/
COPY --from=instrumentor /validator /usr/local/bin/
COPY --from=instrumentor /git/prysm_instrumented/symbols/* /opt/antithesis/symbols/
COPY --from=builder /prysm.version /prysm.version
