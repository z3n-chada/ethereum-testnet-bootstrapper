![etb-all-clients](https://github.com/antithesishq/ethereum-testnet-bootstrapper/actions/workflows/etb-all-clients.yml/badge.svg)

# ethereum-testnet-bootstrapper

## Building images

`make build-all-images`

To rebuild images without cache:

`make rebuild-all-images`

## Building a single image

`source ./common.sh && cd deps/dockers/el && build_image geth geth.Dockerfile`

To rebuild without cache:

`source ./common.sh && cd deps/dockers/el && REBUILD_IMAGES=1 build_image geth geth.Dockerfile`
