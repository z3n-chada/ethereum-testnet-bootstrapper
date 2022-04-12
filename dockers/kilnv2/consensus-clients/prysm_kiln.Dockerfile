FROM golang:1.17-bullseye as prysm_builder


ARG GIT_BRANCH="kiln"
# Update ubuntu
RUN apt-get update && \
        apt-get install -y --no-install-recommends \
        git

RUN mkdir -p /build && mkdir -p /git

WORKDIR /git

ENV GOPATH="/git"


FROM prysm_builder as prysm_validator_builder
# Install prysm
ARG GIT_BRANCH="kiln"

RUN mkdir -p /git/src/github.com/prysmaticlabs/
RUN cd /git/src/github.com/prysmaticlabs/ && \
    git clone --branch "$GIT_BRANCH" \
    --recurse-submodules \
    --depth 1 \
    https://github.com/prysmaticlabs/prysm

# Get dependencies
RUN cd /git/src/github.com/prysmaticlabs/prysm && go get -t -d ./... && go build -o /build ./...

# FROM prysm_builder as prysm_beacon_builder
# # Install prysm
# ARG GIT_BRANCH="kiln"
# 
# RUN mkdir -p /git/src/github.com/prysmaticlabs/
# RUN cd /git/src/github.com/prysmaticlabs/ && \
#     git clone https://github.com/prysmaticlabs/prysm && cd prysm && git checkout b9ffd66bf4d3c24bc97fb6a0a78617b94e068579
# 
# # Get dependencies
# RUN cd /git/src/github.com/prysmaticlabs/prysm && go get -t -d ./... && go build -o /build ./...



FROM debian:bullseye-slim

ARG USER=prysm
ARG UID=10002

RUN apt-get update && apt-get install -y --no-install-recommends \
  ca-certificates curl bash tzdata \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
        apt-get update; \
        apt-get install -y gosu; \
        rm -rf /var/lib/apt/lists/*; \
# verify that the binary works
        gosu nobody true

# See https://stackoverflow.com/a/55757473/12429735RUN
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/prysm" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    "${USER}"

# Create data mount point with permissions
RUN mkdir -p /var/lib/prysm && chown ${USER}:${USER} /var/lib/prysm && chmod 700 /var/lib/prysm

# Copy executable
COPY --from=prysm_validator_builder /build/beacon-chain /usr/local/bin/
COPY --from=prysm_validator_builder /build/validator /usr/local/bin/
COPY --from=prysm_validator_builder /build/client-stats /usr/local/bin/
