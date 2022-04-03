# minimal slim capable of supporting all of the consensus layer clients and execution layer clients
FROM tx-fuzz:kilnv2 as tx_fuzz_builder
FROM debian:bullseye-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre \
    ca-certificates \
    build-essential \
    wget \
    tzdata 

RUN wget https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && dpkg -i packages-microsoft-prod.deb && rm packages-microsoft-prod.deb

RUN apt update && apt install -y dotnet-sdk-6.0 

# add the tx-fuzzer
COPY --from=tx_fuzz_builder /run/tx-fuzz.bin /usr/local/bin/tx-fuzz

ENTRYPOINT ["/bin/bash"]
