FROM chainsafe/lodestar@sha256:f9f741bbccd1b4720ab75390d69f08b717d1ad86abf141edb48bc5dccfd1f170 AS builder

FROM scratch

COPY --from=builder /usr/app /usr/app
COPY --from=builder /git /git

