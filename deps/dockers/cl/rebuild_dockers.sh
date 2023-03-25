

BUILDKIT=1 docker build --no-cache -t nimbus:etb-minimal -f nimbus_minimal.Dockerfile .
BUILDKIT=1 docker build --no-cache -t teku:etb-minimal -f teku_minimal.Dockerfile .
BUILDKIT=1 docker build --no-cache -t lodestar:etb-minimal -f lodestar_minimal.Dockerfile .
BUILDKIT=1 docker build --no-cache -t lighthouse:etb-minimal -f lighthouse_minimal.Dockerfile .
BUILDKIT=1 docker build --no-cache -t prysm:etb-minimal -f prysm_minimal_inst.Dockerfile .
