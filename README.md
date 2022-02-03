# ethereum-testnet-bootstrapper
## Overview
Allows you to easily create and launch custom testnets locally to test various features. You can use dockers provided by client teams or modify and launch your own execution or consensus layer nodes to test and debug.

```
make build-bootstrapper config=/configs/...; make run-bootstrapper config=/configs/...
docker-compose up --force-recreate
```
