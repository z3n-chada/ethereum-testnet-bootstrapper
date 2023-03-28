FROM gcr.io/prysmaticlabs/build-agent as builder

ARG BRANCH="v4.0.0-rc.2"

WORKDIR /git

RUN git clone --branch="${BRANCH}" \
    --recurse-submodules \
    --depth=1 \
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


FROM etb-client-builder:latest as instrumentor

COPY --from=builder /git/prysm /git/prysm
WORKDIR /git

RUN mkdir prysm_instrumented
RUN /opt/antithesis/go_instrumentation/bin/goinstrumentor \
    -logtostderr -stderrthreshold=INFO \
    -antithesis /opt/antithesis/go_instrumentation/instrumentation/go/wrappers \
    prysm prysm_instrumented

WORKDIR /git/prysm_instrumented/customer
RUN go build -tags minimal -o /validator ./cmd/validator
RUN go build -tags minimal -o /beacon-chain ./cmd/beacon-chain

RUN /validator --version
RUN /beacon-chain --version


FROM gcr.io/prysmaticlabs/build-agent as uninstrumented

COPY --from=builder /git/prysm /git/prysm
WORKDIR /git/prysm
# Undo changes we made to pbs and ssz files for instrumentation
RUN git clean --force -d -x && git reset --hard
RUN bazel build --config=minimal \
  //cmd/beacon-chain:beacon-chain \
  //cmd/validator:validator


FROM scratch

COPY --from=instrumentor /beacon-chain /usr/local/bin/
COPY --from=instrumentor /validator /usr/local/bin/
COPY --from=instrumentor /git/prysm_instrumented/symbols/* /opt/antithesis/symbols/
COPY --from=uninstrumented /git/prysm/bazel-bin/cmd/beacon-chain/beacon-chain_/beacon-chain /usr/local/bin/beacon-chain_uninstrumented
COPY --from=uninstrumented /git/prysm/bazel-bin/cmd/validator/validator_/validator /usr/local/bin/validator_uninstrumented
COPY --from=builder /prysm.version /prysm.version