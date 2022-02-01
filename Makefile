.PHONY: clean


build-bootstrapper:
	docker build -t ethereum-testnet-bootstrapper -f Dockerfile .

run-bootstrapper: 
	docker run -it -v $(shell pwd)/:/source/ -v $(shell pwd)/data/:/data ethereum-testnet-bootstrapper --config $(config) --bootstrap-mode

clean:
	rm -r data/*
	rm docker-compose.yaml
