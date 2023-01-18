FROM etb-client-builder:latest as base

FROM base as builder

WORKDIR /git

ARG branch="master"

RUN git clone https://github.com/Consensys/teku.git && \
    cd teku && git checkout "$branch"


RUN cd teku && git log -n 1 --format=format:"%H" > /teku.version
RUN cd teku \
    && ./gradlew distTar installDist

FROM scratch

COPY --from=builder /git/teku/build/install/teku/. /opt/teku/
COPY --from=builder /teku.version /teku.version
