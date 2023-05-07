FROM docker.io/ethpandaops/tx-fuzz as builder


FROM scratch
COPY --from=builder /tx-fuzz.bin /tx-fuzz.bin

ENTRYPOINT ["/tx-fuzz.bin"]