.PHONY: clean

# Build ethereum-testnet-bootstrapper image
build-bootstrapper:
	docker build -t ethereum-testnet-bootstrapper -f bootstrapper.Dockerfile .
rebuild-bootstrapper:
	docker build --no-cache -t ethereum-testnet-bootstrapper -f bootstrapper.Dockerfile .

# Build the etb-all-clients images:
# - etb-all-clients:minimal
# - etb-all-clients:minimal-fuzz
# - etb-all-clients-inst:minimal
build-etb-all-clients:
	cd deps/dockers && ./build_dockers.sh
rebuild-etb-all-clients:
	cd deps/dockers && REBUILD_IMAGES=1 ./build_dockers.sh

build-all-images: build-bootstrapper build-etb-all-clients

# init the testnet dirs and all files needed to later bootstrap the testnet.
init-testnet:
	docker run -it -v $(shell pwd)/:/source/ -v $(shell pwd)/data/:/data ethereum-testnet-bootstrapper --config $(config) --init-testnet

# after an init this runs the bootstrapper and start up the testnet.
run-bootstrapper:
	docker run -it -v $(shell pwd)/:/source/ -v $(shell pwd)/data/:/data ethereum-testnet-bootstrapper --config $(config) --bootstrap-mode

clean:
	docker run -it -v $(shell pwd)/:/source/ -v $(shell pwd)/data/:/data ethereum-testnet-bootstrapper --config $(config) --clear-last-run