# Example local dockers for experiments

# geth client
docker build -t geth-client:master -f geth-client.Dockerfile
# eth2-bootnode
docker build -t bootnode-clients:latest -f bootnode-client.Dockerfile

#pre-bellatrix
docker build -t lighthouse-client:stable -f lighthouse-client_stable.Dockerfile
docker build -t nimbus-client:stable -f nimbus-client_stable.Dockerfile
docker build -t prysm-client:develop -f prysm-client_develop.Dockerfile
docker build -t teku-client:master -f teku-client_master.Dockerfile

# bellatrix dockers.
docker build -t lighthouse-client:kintsugi -f lighthouse-client_kintsugi.Dockerfile
docker build -t nimbus-client:kintsugi -f nimbus-client_kintsugi.Dockerfile
docker build -t prysm-client:kintsugi -f prysm-client_kintsugi.Dockerfile
docker build -t teku-client:kintsugi -f teku-client_kintsugi.Dockerfile
