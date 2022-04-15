FROM golang:1.17 as geth_builder
RUN git clone https://github.com/MariusVanDerWijden/go-ethereum.git \
    && cd go-ethereum && git checkout merge-kiln-bad-block \
    && make geth


FROM debian:bullseye-slim

WORKDIR /geth

ARG USER=geth
ARG UID=10002

# ca-certificates python python3-dev python3-pip gettext-base build-essential && \
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        ca-certificates tzdata  python3-dev && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN adduser \
    --disabled-password \
    --gecos "" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    "${USER}"

COPY --from=geth_builder /go/go-ethereum/build/bin/geth /usr/local/bin/geth

RUN chown -R ${USER}:${USER} /geth
RUN mkdir -p /var/lib/goethereum && chown ${USER}:${USER} /var/lib/goethereum


ENTRYPOINT ["/bin/bash"]

