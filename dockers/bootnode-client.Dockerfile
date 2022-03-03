FROM golang:1.17 as builder

WORKDIR /git

RUN go install github.com/protolambda/eth2-bootnode@latest 

RUN git clone https://github.com/ethereum/go-ethereum.git \
    && cd go-ethereum && git checkout master \
    && make geth && make all

FROM debian:latest

COPY --from=builder /root/go/bin/eth2-bootnode /usr/local/bin/eth2-bootnode
COPY --from=builder /git/go-ethereum/build/bin/geth /usr/local/bin/geth
COPY --from=builder /git/go-ethereum/build/bin/bootnode /usr/local/bin/geth-bootnode

ENTRYPOINT ["/bin/bash"]
