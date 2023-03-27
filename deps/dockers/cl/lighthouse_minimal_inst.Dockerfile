FROM etb-client-builder:latest as builder

RUN apt-get install -y unzip && \
    PB_REL="https://github.com/protocolbuffers/protobuf/releases" && \
    curl -L $PB_REL/download/v3.15.8/protoc-3.15.8-linux-x86_64.zip -o protoc.zip && \
    unzip protoc.zip -d /usr && \
    chmod +x /usr/bin/protoc

WORKDIR /git

RUN git clone https://github.com/sigp/lighthouse.git && cd lighthouse && git checkout capella

# RUN rustup toolchain install nightly
RUN rustup toolchain install nightly
RUN apt update && apt upgrade -y
RUN apt install -y protobuf-compiler libprotobuf-dev

#RUN cd lighthouse && LD_LIBRARY_PATH=/usr/lib/ RUSTFLAGS="-Cpasses=sancov-module -Cllvm-args=-sanitizer-coverage-level=3 -Cllvm-args=-sanitizer-coverage-trace-pc-guard -Ccodegen-units=1 -Cdebuginfo=2 -L/usr/lib/ -lvoidstar" cargo +nightly build --release --manifest-path lighthouse/Cargo.toml --target x86_64-unknown-linux-gnu --features spec-minimal --verbose --bin lighthouse
RUN cd lighthouse && LD_LIBRARY_PATH=/usr/lib/ RUSTFLAGS="-Cpasses=sancov-module -Cllvm-args=-sanitizer-coverage-level=3 -Cllvm-args=-sanitizer-coverage-trace-pc-guard -Ccodegen-units=1 -Cdebuginfo=2 -L/usr/lib/ -lvoidstar" cargo build --release --manifest-path lighthouse/Cargo.toml --target x86_64-unknown-linux-gnu --features spec-minimal --verbose --bin lighthouse
#RUN cd lighthouse && cargo build --release --manifest-path lighthouse/Cargo.toml --target x86_64-unknown-linux-gnu --features spec-minimal --verbose --bin lighthouse_uninstrumented

RUN cd lighthouse && git log -n 1 --format=format:"%H" > /lighthouse.version

FROM scratch

ENV LD_LIBRARY_PATH=/usr/lib/

COPY --from=builder /git/lighthouse/target/x86_64-unknown-linux-gnu/release/lighthouse /usr/local/bin/lighthouse
COPY --from=builder /lighthouse.version /lighthouse.version