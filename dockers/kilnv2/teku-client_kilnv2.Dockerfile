FROM geth:merge-kiln-v2 as geth_builder
FROM besu:main as besu_builder
FROM nethermind:kiln as nethermind_builder
FROM teku:master as teku_builder

FROM base-consensus:latest 

ARG USER=teku
ARG UID=10002

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
COPY --from=teku_builder /opt/teku/. /opt/teku/
# Script to query and store validator key passwords

RUN ln -s /opt/teku/bin/teku /usr/local/bin/teku

# Setup execution clients.
# add geth stuff
COPY --from=geth_builder /usr/local/bin/geth /usr/local/bin/geth
RUN mkdir -p /var/lib/goethereum && chown ${USER}:${USER} /var/lib/goethereum
# add besu 
COPY --from=besu_builder /opt/besu/. /opt/besu
RUN mkdir -p /var/lib/besu && chown -R ${USER}:${USER} /var/lib/besu && chmod -R 700 /var/lib/besu
RUN ln -s /opt/besu/bin/besu /usr/local/bin/besu
# add nethermind 
RUN mkdir /nethermind
COPY --from=nethermind_builder  /nethermind/. .
RUN chown -R ${USER}:${USER} /nethermind
RUN mkdir -p /var/lib/nethermind && chown ${USER}:${USER} /var/lib/nethermind
RUN ln -s  /nethermind/Nethermind.Runner /usr/local/bin/nethermind

WORKDIR /home/teku

# where all of the ethereum-testnet-bootstrapper volumes get mounted in. 
RUN mkdir -p /data && mkdir -p /source && chown -R ${USER}:${USER} /data && chown -R ${USER}:${USER} /source

USER ${USER}

ENTRYPOINT ["/bin/bash"]
