FROM etb-client-builder as builder

# RUN git clone https://github.com/MariusVanDerWijden/go-ethereum.git \
RUN git clone https://github.com/edwards-antithesis/go-ethereum \
    && cd go-ethereum \
    && git checkout ant-merge-bad-block-creator \
    && make geth

FROM etb-client-runner

COPY --from=builder /git/go-ethereum/build/bin/geth /usr/local/bin/geth-bad-block

ENTRYPOINT ["/bin/bash"]
