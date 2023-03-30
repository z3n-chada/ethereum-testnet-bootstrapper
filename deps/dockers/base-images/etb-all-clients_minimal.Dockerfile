# built CL images
FROM lighthouse:etb-minimal AS lh_builder
FROM lodestar:etb-minimal AS ls_builder
FROM nimbus:etb-minimal AS nimbus_builder
FROM teku:etb-minimal AS teku_builder
FROM prysm:etb-minimal AS prysm_builder
# built EL images
FROM besu:etb AS besu_builder
FROM geth:etb AS geth_builder
FROM nethermind:etb AS nethermind_builder

FROM etb-client-runner:latest

COPY --from=geth_builder /usr/local/bin/geth_uninstrumented /usr/local/bin/geth
COPY --from=geth_builder /geth.version /geth.version

COPY --from=besu_builder /opt/besu /opt/besu
COPY --from=besu_builder /besu.version /besu.version
RUN ln -s /opt/besu/bin/besu /usr/local/bin/besu

COPY --from=nethermind_builder /nethermind/ /nethermind/
COPY --from=nethermind_builder /nethermind.version /nethermind.version
RUN ln -s /nethermind/Nethermind.Runner /usr/local/bin/nethermind

COPY --from=lh_builder /usr/local/bin/lighthouse_uninstrumented /usr/local/bin/lighthouse
COPY --from=lh_builder /lighthouse.version /lighthouse.version

COPY --from=nimbus_builder /usr/local/bin/nimbus_beacon_node_uninstrumented /usr/local/bin/nimbus_beacon_node
COPY --from=nimbus_builder /nimbus.version /nimbus.version

COPY --from=prysm_builder /usr/local/bin/beacon-chain_uninstrumented /usr/local/bin/beacon-chain
COPY --from=prysm_builder /usr/local/bin/validator_uninstrumented /usr/local/bin/validator
COPY --from=prysm_builder /prysm.version /prysm.version

COPY --from=teku_builder /opt/teku /opt/teku
COPY --from=teku_builder /teku.version /teku.version
RUN ln -s /opt/teku/bin/teku /usr/local/bin/teku

COPY --from=ls_builder /git/lodestar /git/lodestar
COPY --from=ls_builder /lodestar.version /lodestar.version
RUN ln -s /git/lodestar/node_modules/.bin/lodestar /usr/local/bin/lodestar


ENTRYPOINT ["/bin/bash"]
