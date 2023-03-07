from etb-client-builder:latest as builder

RUN apt-get install -y libsnappy-dev libc6-dev libc6

WORKDIR /git

ARG NETHERMIND_BRANCH="master"

RUN git clone https://github.com/NethermindEth/nethermind && cd nethermind && git checkout ${NETHERMIND_BRANCH}

RUN cd /git/nethermind &&  dotnet publish src/Nethermind/Nethermind.Runner -c release -o out

RUN cd /git/nethermind && git log -n 1 --format=format:"%H" > /nethermind.version

FROM scratch

COPY --from=builder /git/nethermind/out /nethermind/
COPY --from=builder /nethermind.version /nethermind.version
