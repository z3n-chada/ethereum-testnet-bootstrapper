# built CL images
FROM lighthouse_inst:etb-minimal AS lh_builder
FROM lodestar:etb-minimal AS ls_builder
FROM nimbus_inst:etb-minimal AS nimbus_builder
FROM teku:etb-minimal AS teku_builder
FROM prysm_inst:etb-minimal AS prysm_builder
# built EL images
FROM besu:etb AS besu_builder
FROM geth_inst:etb AS geth_builder
FROM nethermind:etb AS nethermind_builder
# built fuzzers
FROM tx-fuzzer:latest AS txfuzzer_builder
FROM geth:bad-block-creator AS geth_bb_builder
FROM prysm:evil-shapella AS prysm_evil_shapella_builder


FROM etb-client-runner:latest

COPY --from=geth_builder /usr/local/bin/geth /usr/local/bin/geth
COPY --from=geth_builder /geth.version /geth.version
COPY --from=geth_builder /opt/antithesis/symbols/* /opt/antithesis/symbols/

COPY --from=besu_builder /opt/besu /opt/besu
COPY --from=besu_builder /besu.version /besu.version
RUN ln -s /opt/besu/bin/besu /usr/local/bin/besu

COPY --from=nethermind_builder /nethermind/ /nethermind/
COPY --from=nethermind_builder /nethermind.version /nethermind.version
RUN ln -s /nethermind/Nethermind.Runner /usr/local/bin/nethermind
# Grab the geth bad block fuzzer
COPY --from=geth_bb_builder /usr/local/bin/geth /usr/local/bin/geth-bad-block
COPY --from=geth_bb_builder /opt/antithesis/symbols/* /opt/antithesis/symbols/
# tx-fuzzer
COPY --from=txfuzzer_builder /tx-fuzz.bin /usr/local/bin/tx-fuzz

# copy in all of the consensus clients
COPY --from=lh_builder /usr/local/bin/lighthouse /usr/local/bin/lighthouse
COPY --from=lh_builder /lighthouse.version /lighthouse.version

COPY --from=nimbus_builder /usr/local/bin/nimbus_beacon_node /usr/local/bin/nimbus_beacon_node
COPY --from=nimbus_builder /nimbus.version /nimbus.version

COPY --from=prysm_builder /usr/local/bin/beacon-chain /usr/local/bin/beacon-chain
COPY --from=prysm_builder /usr/local/bin/validator /usr/local/bin/validator
COPY --from=prysm_builder /prysm.version /prysm.version

COPY --from=teku_builder /opt/teku /opt/teku
COPY --from=teku_builder /teku.version /teku.version
RUN ln -s /opt/teku/bin/teku /usr/local/bin/teku

COPY --from=ls_builder /git/lodestar /git/lodestar
COPY --from=ls_builder /lodestar.version /lodestar.version
RUN ln -s /git/lodestar/node_modules/.bin/lodestar /usr/local/bin/lodestar


ENTRYPOINT ["/bin/bash"]