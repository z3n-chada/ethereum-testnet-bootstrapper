FROM golang:1.17 as builder

WORKDIR /git

RUN go install github.com/protolambda/eth2-bootnode@latest 

RUN git clone https://github.com/ethereum/go-ethereum.git \
    && cd go-ethereum && go run build/ci.go install

FROM debian:latest

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        curl && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /go/bin/eth2-bootnode /usr/local/bin/eth2-bootnode
COPY --from=builder /git/go-ethereum/build/bin/bootnode /usr/local/bin/geth-bootnode
COPY --from=builder /git/go-ethereum/build/bin/geth /usr/local/bin/geth

ENTRYPOINT ["/bin/bash"]
