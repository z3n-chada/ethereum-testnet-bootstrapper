FROM debian:bullseye-slim as base

RUN apt-get update && apt-get install -y git openjdk-17-jdk && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

FROM base as besu_builder

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git

WORKDIR /usr/src 

ARG BESU_BRANCH="main"

RUN git clone --progress https://github.com/hyperledger/besu.git && cd besu && git checkout ${BESU_BRANCH} && ./gradlew installDist

FROM base

# ARG USER=besu
# ARG UID=10001

RUN apt-get update && DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y --no-install-recommends \
  ca-certificates \
  tzdata \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# See https://stackoverflow.com/a/55757473/12429735RUN

# RUN adduser \
#     --disabled-password \
#     --gecos "" \
#     --home "/home/besu" \
#     --shell "/usr/sbin/nologin" \
#     --uid "${UID}" \
#     "${USER}"
# 
# RUN mkdir -p /var/lib/besu && chown -R ${USER}:${USER} /var/lib/besu && chmod -R 700 /var/lib/besu
# 
# # Copy executable
COPY --from=besu_builder /usr/src/besu/build/install/besu/. /opt/besu/
# 
# USER ${USER}

ENTRYPOINT ["/opt/besu/bin/besu"]
