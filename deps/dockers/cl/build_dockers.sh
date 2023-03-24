
# BUILDKIT=1 docker build --registries-conf=`pwd`/../../../registries.conf -t nimbus:etb-minimal -f nimbus_minimal.Dockerfile .
# BUILDKIT=1 docker build --registries-conf=`pwd`/../../../registries.conf -t teku:etb-minimal -f teku_minimal.Dockerfile .
# BUILDKIT=1 docker build --registries-conf=`pwd`/../../../registries.conf -t lodestar:etb-minimal -f lodestar_minimal.Dockerfile .
BUILDKIT=1 docker build --registries-conf=`pwd`/../../../registries.conf -t lighthouse:etb-minimal -f lighthouse_minimal.Dockerfile .
# BUILDKIT=1 docker build --registries-conf=`pwd`/../../../registries.conf -t prysm:etb-minimal -f prysm_minimal.Dockerfile .
