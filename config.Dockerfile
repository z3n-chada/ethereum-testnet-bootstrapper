FROM scratch
ADD deps deps
ADD apps apps
ADD data data
ADD configs configs
ADD entrypoint.sh entrypoint.sh
ADD docker-compose.yaml docker-compose.yaml

 
