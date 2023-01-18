FROM sigp/lighthouse:capella AS builder

FROM scratch

COPY --from=builder /usr/local/bin/lighthouse /usr/local/bin/lighthouse

