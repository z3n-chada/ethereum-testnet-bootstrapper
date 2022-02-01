FROM ubuntu:18.04

WORKDIR /git
LABEL version=kintsugi
LABEL commit=6992eb4261d4582cf12eac46e215c89468613113

RUN apt-get update && apt-get install -y git openjdk-11-jdk && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/Consensys/teku.git && \
    cd /git/teku && git checkout 6992eb4261d4582cf12eac46e215c89468613113 && \
    ./gradlew distTar installDist


RUN ln -s /git/teku/build/install/teku/bin/teku /usr/local/bin/teku

ENTRYPOINT ["/bin/bash"]

# not very minimal but unsure how to move all dependencies for java to use builder copy 
