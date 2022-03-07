FROM scratch
COPY ./ /source
COPY docker-compose.yaml /
COPY data /data

