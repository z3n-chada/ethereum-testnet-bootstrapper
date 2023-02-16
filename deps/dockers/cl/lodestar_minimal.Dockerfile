FROM etb-client-builder AS builder


WORKDIR /git

RUN apt install -y --no-install-recommends python3-dev make g++
RUN ln -s /usr/local/bin/python3 /usr/local/bin/python

RUN npm install --global yarn

RUN git clone https://github.com/ChainSafe/lodestar.git && cd lodestar && git checkout unstable

RUN cd lodestar && git log -n 1 --format=format:"%H" > /lodestar.version

RUN cd /git/lodestar && yarn install --non-interactive --frozen-lockfile && \
  yarn build && \
  yarn install --non-interactive --frozen-lockfile --production

RUN cd /git/lodestar/packages/cli && GIT_COMMIT=${COMMIT} yarn write-git-data

FROM scratch

#ENV VERSION=$VERSION
COPY --from=builder  /git/lodestar /git/lodestar
COPY --from=builder /lodestar.version /lodestar.version
