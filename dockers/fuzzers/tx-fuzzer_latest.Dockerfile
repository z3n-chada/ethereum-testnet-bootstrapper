FROM golang:1.17 as builder
WORKDIR /git
RUN git clone https://github.com/MariusVanDerWijden/go-ethereum.git \
    && cd go-ethereum && git checkout merge-kiln-v2 \
    && make geth

RUN go install github.com/mariusvanderwijden/tx-fuzz/cmd/livefuzzer@latest

FROM debian:latest
WORKDIR /git

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        ca-certificates build-essential python python3-dev python3-pip gettext-base && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install ruamel.yaml web3
# RUN cd /apps && pip3 install -r requirements.txt
COPY --from=builder /git/go-ethereum/build/bin/geth /usr/local/bin/geth
COPY --from=builder /go/bin/livefuzzer /usr/local/bin/livefuzzer


ENTRYPOINT ["/bin/bash"]
