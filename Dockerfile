FROM golang:1.17 as builder

WORKDIR /git

RUN git clone https://github.com/skylenet/eth2-testnet-genesis.git \
    && cd eth2-testnet-genesis && git checkout faster-validator-creation \
    && go install . \
    && go install github.com/wealdtech/ethereal/v2@latest \
    && go install github.com/protolambda/eth2-bootnode@latest 

RUN git clone https://github.com/z3n-chada/eth2-val-tools.git \
    && cd eth2-val-tools && go install ./...

RUN git clone https://github.com/ethereum/go-ethereum.git \
    && cd go-ethereum && git checkout master \
    && make geth && make all

FROM debian:bullseye-slim

WORKDIR /

VOLUME ["/data"]
EXPOSE 8000/tcp
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        ca-certificates build-essential python python3-dev python3-pip gettext-base golang git curl && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


RUN pip3 install ruamel.yaml web3
# RUN cd /apps && pip3 install -r requirements.txt
COPY --from=builder /go/bin/eth2-testnet-genesis /usr/local/bin/eth2-testnet-genesis
COPY --from=builder /go/bin/eth2-val-tools /usr/local/bin/eth2-val-tools
COPY --from=builder /go/bin/eth2-bootnode /usr/local/bin/eth2-bootnode
COPY --from=builder /go/bin/ethereal /usr/local/bin/ethereal
#COPY --from=builder /git/go-ethereum/build/bin/geth /usr/local/bin/geth
COPY --from=builder /git/go-ethereum/build/bin/bootnode /usr/local/bin/bootnode
run chmod +x /usr/local/bin/bootnode
RUN mkdir /configs

COPY ./ /source
COPY configs/ /configs

ENTRYPOINT [ "/source/entrypoint.sh" ]
