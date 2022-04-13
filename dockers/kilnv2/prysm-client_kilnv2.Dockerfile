FROM geth:master as geth_builder
FROM besu:main as besu_builder
FROM nethermind:kiln as nethermind_builder
FROM prysm:kiln as prysm_builder

FROM base-consensus:latest 

ARG USER=prysm
ARG UID=10002

# See https://stackoverflow.com/a/55757473/12429735RUN
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/prysm/" \
    --shell "/usr/sbin/nologin" \
    --uid "${UID}" \
    "${USER}"


RUN apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# in case we want safe environments
RUN mkdir -p /var/lib/prysm && chown ${USER}:${USER} /var/lib/prysm && chmod 700 /var/lib/prysm
# Copy executable
COPY --from=prysm_builder /usr/local/bin/beacon-chain /usr/local/bin/beacon-chain
COPY --from=prysm_builder /usr/local/bin/validator /usr/local/bin/validator
COPY --from=prysm_builder /usr/local/bin/client-stats /usr/local/bin/client-stats

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
COPY --from=nethermind_builder  /nethermind/. /nethermind/
RUN chown -R ${USER}:${USER} /nethermind
RUN mkdir -p /var/lib/nethermind && chown ${USER}:${USER} /var/lib/nethermind
RUN ln -s  /nethermind/Nethermind.Runner /usr/local/bin/nethermind

WORKDIR /home/prysm

# where all of the ethereum-testnet-bootstrapper volumes get mounted in. 
RUN mkdir -p /data && mkdir -p /source && chown -R ${USER}:${USER} /data && chown -R ${USER}:${USER} /source

ENTRYPOINT ["/bin/bash"]
