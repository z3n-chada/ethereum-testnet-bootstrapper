FROM geth:merge-kiln-v2 as geth_builder
FROM besu:main as besu_builder
FROM nethermind:kiln as nethermind_builder
FROM lodestar:master as lodestar_builder

FROM base-consensus:latest 

ARG USER=lodestar
ARG UID=10002

# See https://stackoverflow.com/a/55757473/12429735RUN
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/lodestar/" \
    --shell "/usr/sbin/nologin" \
    --uid "${UID}" \
    "${USER}"

WORKDIR /usr/app

RUN apt update && apt install -y build-essential curl python3-dev make
RUN curl -fsSL https://deb.nodesource.com/setup_current.x | bash -
RUN apt update && apt install -y nodejs 

RUN apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ARG VERSION=next
ENV VERSION=$VERSION
RUN npm install -g npm@8.5.5
RUN npm install @chainsafe/lodestar-cli@$VERSION

RUN chown -R ${USER}:${USER} /usr/app

RUN mkdir -p /var/lib/lodestar/consensus && chown ${USER}:${USER} /var/lib/lodestar/consensus && chmod 700 /var/lib/lodestar/consensus
RUN mkdir -p /var/lib/lodestar/validators && chown ${USER}:${USER} /var/lib/lodestar/validators && chmod 700 /var/lib/lodestar/validators

# RUN ln -s /usr/app/node_modules/.bin/lodestar /usr/local/bin/lodestar
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

WORKDIR /home/lodestar

# where all of the ethereum-testnet-bootstrapper volumes get mounted in. 
RUN mkdir -p /data && mkdir -p /source && chown -R ${USER}:${USER} /data && chown -R ${USER}:${USER} /source

RUN ln -s /usr/app/node_modules/.bin/lodestar /usr/local/bin/lodestar

ENTRYPOINT ["/bin/bash"]
