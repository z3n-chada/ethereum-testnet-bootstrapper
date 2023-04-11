FROM etb-client-builder:latest as builder

ARG BRANCH="master"

WORKDIR /git

RUN git clone --depth=1 --branch="${BRANCH}" https://github.com/NethermindEth/nethermind

WORKDIR /git/nethermind

RUN git log -n 1 --format=format:"%H" > /nethermind.version
RUN dotnet publish src/Nethermind/Nethermind.Runner -c release -o out


FROM scratch

COPY --from=builder /git/nethermind/out /nethermind/
COPY --from=builder /nethermind.version /nethermind.version