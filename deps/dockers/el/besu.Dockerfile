FROM etb-client-builder:latest as builder

ARG BRANCH="main"

WORKDIR /usr/src

RUN git clone --depth=1 --branch="${BRANCH}" https://github.com/hyperledger/besu.git 

WORKDIR /usr/src/besu

RUN git log -n 1 --format=format:"%H" > /besu.version
RUN ./gradlew installDist


FROM scratch

COPY --from=builder /usr/src/besu/build/install/besu/. /opt/besu/
COPY --from=builder /besu.version /besu.version