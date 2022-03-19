ARG DOCKER_TAG="next"

FROM chainsafe/lodestar:${DOCKER_TAG} as lodestar_builder

# Here only to avoid build-time errors
ARG BUILD_TARGET

RUN apk update && apk add --no-cache ca-certificates tzdata bash su-exec && rm -rf /var/cache/apk/*

FROM node:16-bullseye-slim

# Scripts that handle permissions
RUN apt update; apt install -y g++ build-essential nodejs ca-certificates bash tzdata \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

ARG USER=lodestar
ARG UID=10002

# See https://stackoverflow.com/a/55757473/12429735RUN
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/lodestar" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    "${USER}"

RUN mkdir -p /var/lib/lodestar/consensus && chown ${USER}:${USER} /var/lib/lodestar/consensus && chmod 700 /var/lib/lodestar/consensus

RUN mkdir -p /var/lib/lodestar/validators && chown ${USER}:${USER} /var/lib/lodestar/validators && chmod 700 /var/lib/lodestar/validators

WORKDIR /usr/app/

COPY --from=lodestar_builder /usr/app/. .

WORKDIR /home/lodestar

RUN ln -s /usr/app/node_modules/.bin/lodestar /usr/local/bin/lodestar

ENTRYPOINT ["/bin/bash"]
