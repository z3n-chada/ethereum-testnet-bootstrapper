FROM gcr.io/prysmaticlabs/prysm/beacon-chain@sha256:21cdade7443414964eb9089bb9318d0db58940bdcc7e7167f6663277c7072186 AS beacon_builder
FROM gcr.io/prysmaticlabs/prysm/validator@sha256:2081fab4789ab6eeb4e53ff9553bf6db2ec1063bf7c7009b0ce7089be904af0f AS validator_builder

FROM scratch

COPY --from=beacon_builder /app/cmd/beacon-chain/beacon-chain /usr/local/bin/beacon-chain
COPY --from=validator_builder /app/cmd/validator/validator /usr/local/bin/validator

