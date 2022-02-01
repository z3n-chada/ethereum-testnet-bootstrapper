FROM golang:1.17 as builder
RUN git clone https://github.com/skylenet/eth2-testnet-genesis.git \
    && cd eth2-testnet-genesis && git checkout faster-validator-creation \
    && go install . \
    && go install github.com/protolambda/eth2-val-tools@latest \
    && go install github.com/wealdtech/ethereal/v2@latest \
    && go install github.com/protolambda/eth2-bootnode@latest 

FROM debian:latest
WORKDIR /work
VOLUME ["/config", "/data"]
EXPOSE 8000/tcp
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        ca-certificates build-essential python python3-dev python3-pip gettext-base && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install ruamel.yaml web3
# RUN cd /apps && pip3 install -r requirements.txt
COPY --from=builder /go/bin/eth2-testnet-genesis /usr/local/bin/eth2-testnet-genesis
COPY --from=builder /go/bin/eth2-val-tools /usr/local/bin/eth2-val-tools
COPY --from=builder /go/bin/eth2-bootnode /usr/local/bin/eth2-bootnode
COPY --from=builder /go/bin/ethereal /usr/local/bin/ethereal
COPY configs/ /configs
COPY apps /apps
COPY entrypoint.sh .
ENTRYPOINT [ "/work/entrypoint.sh" ]
