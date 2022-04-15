# FROM golang:1.17 as builder
# WORKDIR /git
# RUN git clone https://github.com/MariusVanDerWijden/go-ethereum.git \
#     && cd go-ethereum && git checkout merge-kiln-v2 \
#     && make geth
# 
# 
# FROM kurtosistech/tx-fuzz:0.2.0
# WORKDIR /git
# 
# RUN apk add py3-pip
# RUN apk add bash
# RUN apk add build-base
# RUN pip3 install ruamel.yaml web3
# # RUN cd /apps && pip3 install -r requirements.txt
# COPY --from=builder /git/go-ethereum/build/bin/geth /usr/local/bin/geth
# 
# 
# ENTRYPOINT ["/bin/bash"]

FROM golang:1.17-bullseye AS builder

# We disable CGO here due to:
# 1) https://github.com/golang/go/issues/28065 that prevents 'go test' from running inside an Alpine container
# 2) https://stackoverflow.com/questions/36279253/go-compiled-binary-wont-run-in-an-alpine-docker-container-on-ubuntu-host which
#       which prevents from just switching to the Buster build image
# Sadly, this is slower: https://stackoverflow.com/questions/47714278/why-is-compiling-with-cgo-enabled-0-slower
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    make \
    git


ENV CGO_ENABLED=0

WORKDIR /git
# Copy and download dependencies using go mod
COPY go.mod .
COPY go.sum .
RUN go mod download

# Copy the code into the container
COPY . .

RUN go test ./...

# Build the application
RUN GOOS=linux go build -o tx-fuzz.bin ./cmd/livefuzzer/main.go

# ============= Execution Stage ================
FROM debian:bullseye-slim AS execution

WORKDIR /run

# Copy the code into the container
COPY --from=builder /git/tx-fuzz.bin .

ENTRYPOINT ["./tx-fuzz.bin"]

