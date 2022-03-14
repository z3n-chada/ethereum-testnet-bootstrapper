FROM golang:1.17 as builder

WORKDIR /git

RUN go install github.com/protolambda/eth2-bootnode@latest 

FROM debian:latest

COPY --from=builder /go/bin/eth2-bootnode /usr/local/bin/eth2-bootnode

ENTRYPOINT ["/bin/bash"]
