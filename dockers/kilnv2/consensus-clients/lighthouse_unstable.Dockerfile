FROM rust:1.58.1-bullseye AS lighthouse_builder
WORKDIR /git
RUN apt-get update && apt-get -y upgrade && apt-get install -y cmake libclang-dev
#RUN git clone https://github.com/sigp/lighthouse.git && cd lighthouse && git checkout 381d0ece3cb0b55cc602550549026bf47952de46
RUN git clone https://github.com/sigp/lighthouse.git && cd lighthouse && git checkout unstable
RUN cd lighthouse && make 

from debian:bullseye-slim

ARG USER=lighthouse
ARG UID=10002
# Create data mount point with permissions


# See https://stackoverflow.com/a/55757473/12429735RUN
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/lighthouse" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    "${USER}"

RUN mkdir -p /var/lib/lighthouse/beacon && chown ${USER}:${USER} /var/lib/lighthouse/beacon && chmod 700 /var/lib/lighthouse/beacon
RUN mkdir -p /var/lib/lighthouse/validators && chown ${USER}:${USER} /var/lib/lighthouse/validators && chmod 700 /var/lib/lighthouse/validators

WORKDIR /home/lighthouse

COPY --from=lighthouse_builder /usr/local/cargo/bin/lighthouse /usr/local/bin/lighthouse

ENTRYPOINT ["/bin/bash"]
