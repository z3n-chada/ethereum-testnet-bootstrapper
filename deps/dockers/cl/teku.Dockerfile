FROM consensys/teku:develop as builder

FROM scratch

COPY --from=builder /opt/teku/ /opt/teku/
