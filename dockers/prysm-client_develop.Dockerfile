FROM ubuntu:18.04 as builder

# Update ubuntu
RUN apt-get update && \
	apt-get install -y --no-install-recommends \
		ca-certificates \
		software-properties-common \
		curl \
        wget \
		git \
		clang \
		vim
# Install golang
RUN add-apt-repository ppa:longsleep/golang-backports
RUN apt-get update && \
	apt-get install -y \
	golang

WORKDIR /git


ENV GOPATH="/git"
# Install prysm
# (Hacky way to get specific version in GOPATH mode)
RUN mkdir -p /git/src/github.com/prysmaticlabs/
RUN cd /git/src/github.com/prysmaticlabs/ && \
    git clone \
    --recurse-submodules \
    --depth 1 \
    -b develop \
    https://github.com/prysmaticlabs/prysm

# Get dependencies
RUN cd /git/src/github.com/prysmaticlabs/prysm/ && \
    go get -t -d ./... && \
    go build ./... && \
    go install ./...

FROM debian:latest
LABEL version=develop
LABEL branch=develop

COPY --from=builder /git/bin/beacon-chain /usr/local/bin/beacon-chain
COPY --from=builder /git/bin/validator /usr/local/bin/validator

ENTRYPOINT ["/bin/bash"]
