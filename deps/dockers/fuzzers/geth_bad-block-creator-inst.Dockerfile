FROM etb-client-builder as builder

# RUN git clone https://github.com/edwards-antithesis/go-ethereum \
RUN git clone https://github.com/MariusVanDerWijden/go-ethereum.git \
    && cd go-ethereum \
    && git checkout bad-block-generator \
    && make geth

FROM scratch

COPY --from=builder /git/go-ethereum/build/bin/geth /usr/local/bin/geth-bad-block

ENTRYPOINT ["/bin/bash"]
