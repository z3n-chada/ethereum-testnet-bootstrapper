FROM etb-client-builder:latest as builder

ARG BRANCH="capella"

RUN apt-get install -y unzip && \
    PB_REL="https://github.com/protocolbuffers/protobuf/releases" && \
    curl -L $PB_REL/download/v3.15.8/protoc-3.15.8-linux-x86_64.zip -o protoc.zip && \
    unzip protoc.zip -d /usr && \
    chmod +x /usr/bin/protoc
RUN apt install -y protobuf-compiler libprotobuf-dev

WORKDIR /git

RUN git clone --depth=1 --branch="${BRANCH}" https://github.com/sigp/lighthouse.git

WORKDIR /git/lighthouse

RUN git log -n 1 --format=format:"%H" > /lighthouse.version
RUN cargo build --release --manifest-path lighthouse/Cargo.toml --target x86_64-unknown-linux-gnu --features spec-minimal --bin lighthouse
RUN mv target/x86_64-unknown-linux-gnu/release/lighthouse /tmp/lighthouse_uninstrumented
RUN cargo clean
RUN LD_LIBRARY_PATH=/usr/lib/ RUSTFLAGS="-Cpasses=sancov-module -Cllvm-args=-sanitizer-coverage-level=3 -Cllvm-args=-sanitizer-coverage-trace-pc-guard -Ccodegen-units=1 -Cdebuginfo=2 -L/usr/lib/ -lvoidstar" cargo build --release --manifest-path lighthouse/Cargo.toml --target x86_64-unknown-linux-gnu --features spec-minimal --bin lighthouse


FROM scratch

ENV LD_LIBRARY_PATH=/usr/lib/
COPY --from=builder /git/lighthouse/target/x86_64-unknown-linux-gnu/release/lighthouse /usr/local/bin/lighthouse
COPY --from=builder /tmp/lighthouse_uninstrumented /usr/local/bin/lighthouse_uninstrumented
COPY --from=builder /lighthouse.version /lighthouse.version