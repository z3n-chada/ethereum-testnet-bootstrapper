from etb-client-builder:latest as builder

run apt-get install -y unzip && \
    PB_REL="https://github.com/protocolbuffers/protobuf/releases" && \
    curl -L $PB_REL/download/v3.15.8/protoc-3.15.8-linux-x86_64.zip -o protoc.zip && \
    unzip protoc.zip -d /usr && \
    chmod +x /usr/bin/protoc

workdir /git

run git clone https://github.com/sigp/lighthouse.git && cd lighthouse && git checkout stable

run rustup toolchain install stable

run cd lighthouse && LD_LIBRARY_PATH=/usr/lib/ RUSTFLAGS="-Cpasses=sancov-module -Cllvm-args=-sanitizer-coverage-level=3 -Cllvm-args=-sanitizer-coverage-trace-pc-guard -Ccodegen-units=1 -Cdebuginfo=2 -L/usr/lib/ -lvoidstar" cargo +stable build --release --manifest-path lighthouse/Cargo.toml --target x86_64-unknown-linux-gnu --features modern --verbose --bin lighthouse
run cd lighthouse && git log -n 1 --format=format:"%H" > /lighthouse.version

from etb-client-runner:latest

ENV LD_LIBRARY_PATH=/usr/lib/

COPY --from=builder /git/lighthouse/target/x86_64-unknown-linux-gnu/release/lighthouse /usr/local/bin/lighthouse
COPY --from=builder /lighthouse.version /lighthouse.version

ENTRYPOINT ["/bin/bash"]
