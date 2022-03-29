# minimal slim capable of supporting all of the consensus layer clients and execution layer clients
FROM debian:bullseye-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre \
    ca-certificates \
    build-essential \
    wget \
    tzdata 

RUN wget https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && dpkg -i packages-microsoft-prod.deb && rm packages-microsoft-prod.deb

RUN apt update && apt install -y dotnet-sdk-6.0 

ENTRYPOINT ["/bin/bash"]
