FROM consensys/teku:23.3.1 as builder

FROM scratch

COPY --from=builder /opt/teku/ /opt/teku/
