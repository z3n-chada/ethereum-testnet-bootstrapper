FROM ethpandaops/geth:withdrawals-timestamp-6ab6d73 AS builder

FROM scratch

COPY --from=builder /usr/local/bin/geth /usr/local/bin/geth

