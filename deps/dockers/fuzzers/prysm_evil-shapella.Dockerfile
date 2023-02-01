FROM etb-client-builder:latest as base

FROM base as builder

WORKDIR /git

ARG GIT_BRANCH="evil-shapella"

RUN mkdir -p /git/src/github.com/prysmaticlabs/
RUN mkdir -p /build

RUN cd /git/src/github.com/prysmaticlabs/ && \
    git clone --branch "$GIT_BRANCH" \
    --recurse-submodules \
    --depth 1 \
    https://github.com/prysmaticlabs/prysm

WORKDIR /git/src/github.com/prysmaticlabs/prysm
RUN git log -n 1 --format=format:"%H" > /prysm.version

RUN cd /git/src/github.com/prysmaticlabs/prysm && go get -t -d ./...

#Build with instrumentation
RUN cd /git/src/github.com/prysmaticlabs/prysm && go build -o /build ./...
RUN go env GOPATH

FROM scratch

COPY --from=builder /build/beacon-chain /usr/local/bin/beacon-chain_evil-shapella
COPY --from=builder /prysm.version /prysm_evil-shapella.version
