FROM debian:bullseye-slim
# We use clang as the compiler
# we build a nodejs+go+rust+dotnet env
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpcre3-dev \
    lsb-release \
    software-properties-common \
    apt-transport-https \
    openjdk-17-jdk \
    ca-certificates \
    wget \
    tzdata \
    bash \
    python3-dev \
    gnupg \
    cmake \
    libc6-dev \
    libsnappy-dev \
    git

# set up dotnet
RUN wget https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && dpkg -i packages-microsoft-prod.deb && rm packages-microsoft-prod.deb
RUN apt update && apt install -y dotnet-sdk-7.0

# set up clang 14
WORKDIR /git

RUN wget --no-check-certificate https://apt.llvm.org/llvm.sh && chmod +x llvm.sh && ./llvm.sh 14

ENV LLVM_CONFIG=llvm-config-14

# set up go
RUN wget https://go.dev/dl/go1.18.3.linux-amd64.tar.gz
RUN tar -zxvf go1.18.3.linux-amd64.tar.gz -C /usr/local/
RUN ln -s /usr/local/go/bin/go /usr/local/bin/go
RUN ln -s /usr/local/go/bin/gofmt /usr/local/bin/gofmt

# set up nodejs
# Install nodejs
run apt update \
    && apt install curl ca-certificates -y --no-install-recommends \
    && curl -sL https://deb.nodesource.com/setup_18.x | bash -

run apt-get update && apt-get install -y --no-install-recommends nodejs 

# set up cargo/rustc with nightly
# reference: https://github.com/rust-lang/docker-rust/blob/59ffcf40eed2aca0160790f0ae2f0288868e0291/1.60.0/bullseye/Dockerfile
ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH \
    RUST_VERSION=1.58.1

RUN set -eux; \
    dpkgArch="$(dpkg --print-architecture)"; \
    case "${dpkgArch##*-}" in \
        amd64) rustArch='x86_64-unknown-linux-gnu'; rustupSha256='3dc5ef50861ee18657f9db2eeb7392f9c2a6c95c90ab41e45ab4ca71476b4338' ;; \
        armhf) rustArch='armv7-unknown-linux-gnueabihf'; rustupSha256='67777ac3bc17277102f2ed73fd5f14c51f4ca5963adadf7f174adf4ebc38747b' ;; \
        arm64) rustArch='aarch64-unknown-linux-gnu'; rustupSha256='32a1532f7cef072a667bac53f1a5542c99666c4071af0c9549795bbdb2069ec1' ;; \
        i386) rustArch='i686-unknown-linux-gnu'; rustupSha256='e50d1deb99048bc5782a0200aa33e4eea70747d49dffdc9d06812fd22a372515' ;; \
        *) echo >&2 "unsupported architecture: ${dpkgArch}"; exit 1 ;; \
    esac; \
    url="https://static.rust-lang.org/rustup/archive/1.24.3/${rustArch}/rustup-init"; \
    wget "$url"; \
    echo "${rustupSha256} *rustup-init" | sha256sum -c -; \
    chmod +x rustup-init; \
    ./rustup-init -y --no-modify-path --profile minimal --default-toolchain ${RUST_VERSION} --default-host ${rustArch}; \
    rm rustup-init; \
    chmod -R a+w $RUSTUP_HOME $CARGO_HOME; \
    rustup --version; \
    cargo --version; \
    rustc --version;

# build the rocksdb 
RUN git clone https://github.com/facebook/rocksdb.git
RUN cd rocksdb && make -j32 install

# Antithesis instrumentation resources
COPY lib/libvoidstar.so /usr/lib/libvoidstar.so
RUN mkdir -p /opt/antithesis/
COPY go_instrumentation /opt/antithesis/go_instrumentation


ENTRYPOINT ["/bin/bash"]
