FROM consensys/teku:23.3.1 as builder

RUN /opt/teku/bin/teku --version | awk -F/ '{ print $2 }' > /teku.version


FROM scratch

COPY --from=builder /opt/teku/ /opt/teku/
COPY --from=builder /teku.version /teku.version