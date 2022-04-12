FROM debian:bullseye as base

RUN apt-get update && apt-get install -y git openjdk-11-jdk && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

FROM base as teku_builder

WORKDIR /git

ARG branch="master"

RUN apt install git 

RUN git clone https://github.com/Consensys/teku.git && \
    cd teku && git checkout "$branch" && \
    ./gradlew distTar installDist

FROM base

WORKDIR /teku

ARG USER=teku
ARG UID=10002

RUN apt-get update && apt-get install -y --no-install-recommends \
  ca-certificates \
  tzdata \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
        apt-get update; \
        apt-get install -y gosu; \
        rm -rf /var/lib/apt/lists/*; \
# verify that the binary works
        gosu nobody true

# See https://stackoverflow.com/a/55757473/12429735RUN
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/teku/" \
    --shell "/usr/sbin/nologin" \
    --uid "${UID}" \
    "${USER}"

RUN mkdir -p /var/lib/teku/validator-keys && mkdir -p /var/lib/teku/validator-passwords && chown -R ${USER}:${USER} /var/lib/teku && chmod -R 700 /var/lib/teku


# Copy executable
COPY --from=teku_builder /git/teku/build/install/teku/. /opt/teku/
# Script to query and store validator key passwords

RUN ln -s /opt/teku/bin/teku /usr/local/bin/teku

ENTRYPOINT ["teku"]


