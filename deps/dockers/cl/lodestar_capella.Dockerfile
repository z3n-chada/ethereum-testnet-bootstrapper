FROM etb-client-builder AS builder

WORKDIR /usr/app
RUN apt install -y --no-install-recommends python3-dev make g++
RUN ln -s /usr/local/bin/python3 /usr/local/bin/python
ARG VERSION=next
ENV VERSION=$VERSION
RUN npm install -g npm@8.8.0
RUN npm install @chainsafe/lodestar-cli@$VERSION

FROM scratch

ENV VERSION=$VERSION
COPY --from=builder /usr/app /usr/app

