FROM gcr.io/prysmaticlabs/build-agent AS builder

ARG BRANCH="evil-shapella"

WORKDIR /git

RUN git clone --depth 1 --branch="${BRANCH}" \
    --recurse-submodules \
    https://github.com/prysmaticlabs/prysm

WORKDIR /git/prysm

RUN git log -n 1 --format=format:"%H" > /prysm.version
# Build binaries for minimal configuration.
RUN bazel build --config=minimal \
  //cmd/beacon-chain:beacon-chain \
  //cmd/validator:validator


FROM scratch

COPY --from=builder /git/prysm/bazel-bin/cmd/beacon-chain/beacon-chain_/beacon-chain /usr/local/bin/beacon-chain
COPY --from=builder /git/prysm/bazel-bin/cmd/validator/validator_/validator /usr/local/bin/validator
COPY --from=builder /prysm.version /prysm_evil-shapella.version