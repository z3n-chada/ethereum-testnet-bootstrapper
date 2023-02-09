# custom ethdo
FROM golang:1.18 as go_builder

RUN go install github.com/0xTylerHolmes/ethdo@fuzz

# built CL images
FROM lighthouse:etb-minimal-fuzz AS lh_builder
FROM prysm:etb-minimal-fuzz AS prysm_builder

# built fuzzers
FROM tx-fuzzer:latest AS txfuzzer_builder
FROM geth:bad-block-creator AS geth_bb_builder

FROM etb-client-runner:latest as base

COPY --from=geth_bb_builder /usr/local/bin/geth /usr/local/bin/geth
COPY --from=geth_bb_builder /geth.version /geth.version

# tx-fuzzer
COPY --from=txfuzzer_builder /run/tx-fuzz.bin /usr/local/bin/tx-fuzz

# copy in all of the consensus clients
COPY --from=lh_builder /usr/local/bin/lighthouse /usr/local/bin/lighthouse
COPY --from=lh_builder /lighthouse.version /lighthouse.version

COPY --from=prysm_builder /usr/local/bin/beacon-chain /usr/local/bin/beacon-chain
COPY --from=prysm_builder /usr/local/bin/validator /usr/local/bin/validator

# ethdo fuzzer
COPY --from=go_builder /go/bin/ethdo /usr/local/bin/ethdo

ENTRYPOINT ["/bin/bash"]
