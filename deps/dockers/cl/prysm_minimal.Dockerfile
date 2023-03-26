FROM gcr.io/prysmaticlabs/build-agent AS builder

WORKDIR /git

RUN git clone --branch v4.0.0-rc.2 \
    --recurse-submodules \
    --depth 1 \
    https://github.com/prysmaticlabs/prysm

WORKDIR /git/prysm
RUN git log -n 1 --format=format:"%H" > /prysm.version

# Build binaries for minimal configuration.
RUN bazel build --config=minimal \
  //cmd/beacon-chain:beacon-chain \
  //cmd/validator:validator



FROM scratch

COPY --from=builder /git/prysm/bazel-bin/cmd/beacon-chain/beacon-chain_/beacon-chain /usr/local/bin/
COPY --from=builder /git/prysm/bazel-bin/cmd/validator/validator_/validator /usr/local/bin/
COPY --from=builder /prysm.version /prysm.version
