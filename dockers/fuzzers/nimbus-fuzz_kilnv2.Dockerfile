FROM geth-bad-block:merge-kiln-bad-block as geth_builder
FROM nimbus:kiln-dev-auth as nimbus_builder

FROM base-consensus:latest 

ARG USER=nimbus
ARG UID=10002

# See https://stackoverflow.com/a/55757473/12429735RUN
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/nimbus/" \
    --shell "/usr/sbin/nologin" \
    --uid "${UID}" \
    "${USER}"

# Copy executable
COPY --from=nimbus_builder /usr/local/bin/nimbus_beacon_node /usr/local/bin/nimbus_beacon_node
COPY --from=nimbus_builder /usr/local/bin/nimbus_validator_client /usr/local/bin/nimbus_validator_client

# Setup execution clients.
# add geth stuff
COPY --from=geth_builder /usr/local/bin/geth /usr/local/bin/geth
RUN mkdir -p /var/lib/goethereum && chown ${USER}:${USER} /var/lib/goethereum

WORKDIR /home/nimbus

# where all of the ethereum-testnet-bootstrapper volumes get mounted in. 
RUN mkdir -p /data && mkdir -p /source && chown -R ${USER}:${USER} /data && chown -R ${USER}:${USER} /source


ENTRYPOINT ["/bin/bash"]
