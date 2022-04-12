# Build Nimbus in a stock debian container
FROM debian:bullseye-slim as nimbus_builder

WORKDIR /git
# Included here to avoid build-time complaints
ARG BRANCH="kiln-dev-auth"

RUN apt-get update && apt-get install -y build-essential git libpcre3-dev ca-certificates wget lsb-release wget software-properties-common

RUN wget --no-check-certificate https://apt.llvm.org/llvm.sh && chmod +x llvm.sh && ./llvm.sh 13

ENV LLVM_CONFIG=llvm-config-13

RUN git clone https://github.com/status-im/nimbus-eth2.git

RUN cd nimbus-eth2 && git checkout ${BRANCH}

RUN cd nimbus-eth2 && make -j64 nimbus_beacon_node NIMFLAGS="--cc:clang --clang.exe:clang-13 --clang.linkerexe:clang-13" \
                   && make -j64 nimbus_validator_client NIMFLAGS="--cc:clang --clang.exe:clang-13 --clang.linkerexe:clang-13"

# Pull all binaries into a second stage deploy debian container
FROM debian:bullseye-slim

ARG USER="nimbus"
ARG UID=10002

RUN apt-get update && DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y --no-install-recommends \
  ca-certificates bash tzdata nim \
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
    --home "/home/nimbus" \
    --shell "/usr/sbin/nologin" \
    --uid "${UID}" \
    "${USER}"


RUN mkdir -p /var/lib/nimbus && chown ${USER}:${USER} /var/lib/nimbus && chmod 700 /var/lib/nimbus

# Copy executable
RUN mkdir -p /git/nimbus-eth2/
COPY --from=nimbus_builder /git/nimbus-eth2/build/nimbus_beacon_node /usr/local/bin/nimbus_beacon_node
COPY --from=nimbus_builder /git/nimbus-eth2/build/nimbus_validator_client /usr/local/bin/nimbus_validator_client
COPY --from=nimbus_builder /git/nimbus-eth2/ /git/nimbus-eth2/

USER ${USER}

ENTRYPOINT ["/bin/bash"]
