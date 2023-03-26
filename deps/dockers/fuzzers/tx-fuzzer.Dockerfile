FROM etb-client-builder AS builder

# We disable CGO here due to:
# 1) https://github.com/golang/go/issues/28065 that prevents 'go test' from running inside an Alpine container
# 2) https://stackoverflow.com/questions/36279253/go-compiled-binary-wont-run-in-an-alpine-docker-container-on-ubuntu-host which
#       which prevents from just switching to the Buster build image
# Sadly, this is slower: https://stackoverflow.com/questions/47714278/why-is-compiling-with-cgo-enabled-0-slower

ENV CGO_ENABLED=0

WORKDIR /git
# Copy and download dependencies using go mod

RUN git clone -b master https://github.com/MariusVanDerWijden/tx-fuzz

WORKDIR /git/tx-fuzz/cmd/livefuzzer

RUN GOOS=linux go build -o tx-fuzz.bin
# RUN GOOS=linux go build -o tx-fuzz.bin ./cmd/livefuzzer/*

FROM debian:bullseye-slim

WORKDIR /run

# Copy the code into the container
COPY --from=builder /git/tx-fuzz/cmd/livefuzzer/tx-fuzz.bin .

ENTRYPOINT ["./tx-fuzz.bin"]

