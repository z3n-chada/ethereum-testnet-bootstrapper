FROM geth-bad-block:merge-kiln-bad-block as geth_builder
FROM lighthouse:unstable as lighthouse_builder

FROM base-consensus:latest 

ARG USER=lighthouse
ARG UID=10002

# See https://stackoverflow.com/a/55757473/12429735RUN
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/lighthouse/" \
    --shell "/usr/sbin/nologin" \
    --uid "${UID}" \
    "${USER}"

# in case we run "safe" examples.
RUN mkdir -p /var/lib/lighthouse/beacon && chown ${USER}:${USER} /var/lib/lighthouse/beacon && chmod 700 /var/lib/lighthouse/beacon
RUN mkdir -p /var/lib/lighthouse/validators && chown ${USER}:${USER} /var/lib/lighthouse/validators && chmod 700 /var/lib/lighthouse/validators

# Copy executable
COPY --from=lighthouse_builder /usr/local/bin/lighthouse /usr/local/bin/lighthouse

# Setup execution clients.
# add geth stuff
COPY --from=geth_builder /usr/local/bin/geth /usr/local/bin/geth
RUN mkdir -p /var/lib/goethereum && chown ${USER}:${USER} /var/lib/goethereum
# add besu 

WORKDIR /home/lighthouse

# where all of the ethereum-testnet-bootstrapper volumes get mounted in. 
RUN mkdir -p /data && mkdir -p /source && chown -R ${USER}:${USER} /data && chown -R ${USER}:${USER} /source

ENTRYPOINT ["/bin/bash"]
