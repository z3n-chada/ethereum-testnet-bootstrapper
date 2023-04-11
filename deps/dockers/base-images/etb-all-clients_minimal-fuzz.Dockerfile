# custom ethdo
FROM golang:1.18 as go_builder

RUN go install github.com/0xTylerHolmes/ethdo@fuzz


# built CL images
FROM lighthouse:etb-minimal-fuzz AS lh_builder
FROM prysm:etb-minimal-fuzz AS prysm_builder

# built fuzzers
FROM tx-fuzzer:latest AS txfuzzer_builder
FROM geth:bad-block-creator AS geth_bb_builder


FROM etb-client-runner:latest

COPY --from=geth_bb_builder /usr/local/bin/geth_uninstrumented /usr/local/bin/geth
COPY --from=geth_bb_builder /geth_bb.version /geth_bb.version

COPY --from=txfuzzer_builder /tx-fuzz.bin /usr/local/bin/tx-fuzz

COPY --from=lh_builder /usr/local/bin/lighthouse /usr/local/bin/lighthouse
COPY --from=lh_builder /lighthouse_fuzz.version /lighthouse_fuzz.version

COPY --from=prysm_builder /usr/local/bin/beacon-chain /usr/local/bin/beacon-chain
COPY --from=prysm_builder /usr/local/bin/validator /usr/local/bin/validator
COPY --from=prysm_builder /prysm_evil-shapella.version /prysm_evil-shapella.version

# ethdo fuzzer
COPY --from=go_builder /go/bin/ethdo /usr/local/bin/ethdo

ENTRYPOINT ["/bin/bash"]