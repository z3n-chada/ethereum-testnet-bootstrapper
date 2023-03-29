FROM etb-client-builder AS builder

ARG BRANCH="unstable"

RUN apt install -y --no-install-recommends python3-dev make g++
RUN ln -s /usr/local/bin/python3 /usr/local/bin/python
RUN npm install --global yarn

WORKDIR /git

RUN git clone --depth=1 --branch="${BRANCH}" https://github.com/ChainSafe/lodestar.git

WORKDIR /git/lodestar

RUN git log -n 1 --format=format:"%H" > /lodestar.version
RUN yarn install --non-interactive --frozen-lockfile && \
  yarn build && \
  yarn install --non-interactive --frozen-lockfile --production
RUN cd packages/cli && yarn write-git-data


FROM scratch

COPY --from=builder /git/lodestar /git/lodestar
COPY --from=builder /lodestar.version /lodestar.version