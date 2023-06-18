.PHONY: clean
log_level ?= "info"
# Build ethereum-testnet-bootstrapper image
build-bootstrapper:
	docker build -t ethereum-testnet-bootstrapper -f bootstrapper.Dockerfile .
rebuild-bootstrapper:
	docker build --no-cache -t ethereum-testnet-bootstrapper -f bootstrapper.Dockerfile .

# Build the etb-all-clients images:
# - etb-all-clients:minimal-current
# - etb-all-clients:minimal-next  <- untested
# - etb-all-clients:mainnet-current
# - etb-all-clients:mainnet-next
build-etb-all-clients:
	cd deps/dockers && ./build-dockers.sh

# a rebuild uses --no-cache in the docker build step.
rebuild-etb-all-clients:
	cd deps/dockers && REBUILD_IMAGES=1 ./build-dockers.sh

build-all-images: build-bootstrapper build-etb-all-clients
rebuild-all-images: rebuild-bootstrapper rebuild-etb-all-clients

# init the testnet dirs and all files needed to later bootstrap the testnet.
init-testnet:
	docker run -it -v $(shell pwd)/:/source/ -v $(shell pwd)/data/:/data ethereum-testnet-bootstrapper --config $(config) --init-testnet --log-level $(log_level)

# after an init this runs the bootstrapper and start up the testnet.
run-bootstrapper:
	docker run -it -v $(shell pwd)/:/source/ -v $(shell pwd)/data/:/data ethereum-testnet-bootstrapper --config $(config) --bootstrap-mode

# remove last run.
clean:
	docker run -t -v $(shell pwd)/:/source/ -v $(shell pwd)/data/:/data ethereum-testnet-bootstrapper --clean --log-level $(log_level)