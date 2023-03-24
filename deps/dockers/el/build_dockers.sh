

BUILDKIT=1 docker build -t geth:etb -f geth.Dockerfile .
BUILDKIT=1 docker build -t besu:etb -f besu.Dockerfile .
BUILDKIT=1 docker build -t nethermind:etb -f nethermind.Dockerfile .
