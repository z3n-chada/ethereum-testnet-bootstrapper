FROM ubuntu:18.04 as builder

# Update ubuntu
RUN apt-get update && \
	apt-get install -y --no-install-recommends \
		ca-certificates \
		software-properties-common \
		curl \
        wget \
		git \
		clang \
		vim
# Install golang
RUN add-apt-repository ppa:longsleep/golang-backports
RUN apt-get update && \
	apt-get install -y \
	golang

WORKDIR /git

RUN git clone https://github.com/protolambda/eth2-bootnode.git

RUN cd /git/eth2-bootnode && go install .

FROM debian:latest

COPY --from=builder /root/go/bin/eth2-bootnode /usr/local/bin/eth2-bootnode

ENTRYPOINT ["/bin/bash"]
