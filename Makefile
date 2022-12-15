.PHONY: clean

# build the ethereum-testnet-bootstrapper docker.
build-bootstrapper:
	docker build -t ethereum-testnet-bootstrapper -f Dockerfile .

# init the testnet dirs and all files needed to later bootstrap the testnet.
init-testnet:
	docker run -it -v $(shell pwd)/:/source/ -v $(shell pwd)/data/:/data ethereum-testnet-bootstrapper --config $(config) --init-testnet

run-bootstrapper:
	docker run -it -v $(shell pwd)/:/source/ -v $(shell pwd)/data/:/data ethereum-testnet-bootstrapper --config $(config) --bootstrap-mode
build-dockers:
	cd etb-dockers && ./build_dockers.sh

clean:
	docker run -it -v $(shell pwd)/:/source/ -v $(shell pwd)/data/:/data ethereum-testnet-bootstrapper --config $(config) --clear-last-run
	rm docker-compose.yaml

