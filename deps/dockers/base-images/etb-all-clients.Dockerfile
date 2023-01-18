# built CL images
FROM lighthouse:etb as lh_builder
FROM lodestar:etb as ls_builder
FROM nimbus:etb as nimbus_builder
FROM teku:etb as teku_builder
FROM prysm:etb as prysm_builder
# built EL images
FROM besu:etb as besu_builder
FROM geth:etb as geth_builder
FROM nethermind:etb as nethermind_builder
# built fuzzers
FROM tx-fuzzer:latest as txfuzzer_builder
FROM geth:bad-block-creator as geth_bb_builder

FROM etb-client-runner:latest as base

COPY --from=geth_builder /usr/local/bin/geth /usr/local/bin/geth
COPY --from=geth_builder /usr/local/bin/bootnode /usr/local/bin/bootnode
COPY --from=geth_builder /geth.version /geth.version
COPY --from=besu_builder /opt/besu /opt/besu
COPY --from=besu_builder /besu.version /besu.version
RUN ln -s /opt/besu/bin/besu /usr/local/bin/besu
COPY --from=nethermind_builder /nethermind/ /nethermind/
COPY --from=nethermind_builder /nethermind.version /nethermind.version
RUN ln -s /nethermind/Nethermind.Runner /usr/local/bin/nethermind
# Grab the geth bad block fuzzer
COPY --from=geth_bb_builder /usr/local/bin/geth-bad-block /usr/local/bin/geth-bad-block

#COPY --from=txfuzzer_builder /run/tx-fuzz.bin /usr/local/bin/tx-fuzz
#COPY --from=geth_bad_block_builder /usr/local/bin/geth-bad-block /usr/local/bin/geth-bad-block-creator
#COPY --from=erigon_builder /usr/local/bin/erigon /usr/local/bin/erigon
##COPY --from=erigon_builder /erigon.version /erigon.version

# copy in all of the consensus clients
COPY --from=lh_builder /usr/local/bin/lighthouse /usr/local/bin/lighthouse
COPY --from=lh_builder /lighthouse.version /lighthouse.version
COPY --from=nimbus_builder /usr/local/bin/nimbus_beacon_node /usr/local/bin/nimbus_beacon_node
#COPY --from=nimbus_builder /usr/local/bin/nimbus_validator_client /usr/local/bin/nimbus_validator_client
COPY --from=nimbus_builder /nimbus.version /nimbus.version
COPY --from=prysm_builder /usr/local/bin/beacon-chain /usr/local/bin/beacon-chain
COPY --from=prysm_builder /usr/local/bin/validator /usr/local/bin/validator
COPY --from=prysm_builder /prysm.version /prysm.version
COPY --from=teku_builder /opt/teku /opt/teku
COPY --from=teku_builder /teku.version /teku.version
RUN ln -s /opt/teku/bin/teku /usr/local/bin/teku
COPY --from=ls_builder /usr/app/ /usr/app/
RUN ln -s /usr/app/node_modules/.bin/lodestar /usr/local/bin/lodestar

ENTRYPOINT ["/bin/bash"]