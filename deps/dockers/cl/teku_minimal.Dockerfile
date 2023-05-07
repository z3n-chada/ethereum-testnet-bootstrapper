FROM consensys/teku:23.3.1 as builder

RUN /opt/teku/bin/teku --version | awk -F/ '{ print $2 }' > /tmp/teku.version


FROM scratch

COPY --from=builder /opt/teku/ /opt/teku/
COPY --from=builder /tmp/teku.version /teku.version
