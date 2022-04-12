FROM debian:bullseye as nethermind_builder

ARG NETHERMIND_BRANCH="kiln"

WORKDIR /git

RUN apt update && apt install -y libsnappy-dev libc6-dev libc6 apt-transport-https wget git
 
RUN wget https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && dpkg -i packages-microsoft-prod.deb && rm packages-microsoft-prod.deb

RUN apt update && apt install -y dotnet-sdk-6.0

RUN git clone https://github.com/NethermindEth/nethermind && cd nethermind && git checkout "$NETHERMIND_BRANCH" && git submodule update --init src/Dirichlet src/int256 src/rocksdb-sharp src/Math.Gmp.Native 

RUN cd /git/nethermind &&  dotnet publish src/Nethermind/Nethermind.Runner -c release -o out

FROM debian:bullseye-slim

ARG USER=nethermind
ARG UID=10002

RUN apt-get update && apt-get install -y --no-install-recommends \
  ca-certificates curl bash tzdata libsnappy-dev libc6-dev apt-transport-https wget \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN wget https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && dpkg -i packages-microsoft-prod.deb && rm packages-microsoft-prod.deb

RUN apt-get update && apt-get install -y --no-install-recommends aspnetcore-runtime-6.0 

RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/nethermind" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    "${USER}"

WORKDIR /nethermind

COPY --from=nethermind_builder /git/nethermind/out .

RUN chown -R ${USER}:${USER} /nethermind
RUN mkdir -p /var/lib/nethermind && chown ${USER}:${USER} /var/lib/nethermind

RUN chmod +x Nethermind.Runner

USER ${USER}

ENTRYPOINT ["./Nethermind.Runner"]
