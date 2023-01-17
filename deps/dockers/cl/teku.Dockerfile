FROM etb-client-builder:latest as base

FROM base as builder

WORKDIR /git

ARG branch="master"

RUN git clone https://github.com/Consensys/teku.git && \
    cd teku && git checkout "$branch"


RUN cd teku && git log -n 1 --format=format:"%H" > /teku.version
RUN cd teku \
    && ./gradlew distTar installDist

FROM debian:bullseye-slim

RUN apt update && apt install -y --no-install-recommends \
    openjdk-17-jre 

RUN mkdir -p /opt/teku

COPY --from=builder /git/teku/build/install/teku/. /opt/teku/
COPY --from=builder /teku.version /teku.version

RUN ln -s /opt/teku/bin/teku /usr/local/bin/teku

ENTRYPOINT ["/bin/bash"]
