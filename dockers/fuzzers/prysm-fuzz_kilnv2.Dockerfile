FROM geth-bad-block:merge-kiln-bad-block as geth_builder
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

WORKDIR /home/prysm

# where all of the ethereum-testnet-bootstrapper volumes get mounted in. 
RUN mkdir -p /data && mkdir -p /source && chown -R ${USER}:${USER} /data && chown -R ${USER}:${USER} /source

ENTRYPOINT ["/bin/bash"]
