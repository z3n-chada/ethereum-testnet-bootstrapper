
echo "<<<<<<<<<< ANTITHESIS >>>>>>>>>> - Building GETH"
BUILDKIT=1 docker build -t geth:etb -f geth.Dockerfile .
echo "<<<<<<<<<< ANTITHESIS >>>>>>>>>> - Building BESU"
BUILDKIT=1 docker build -t besu:etb -f besu.Dockerfile .
echo "<<<<<<<<<< ANTITHESIS >>>>>>>>>> - Building NETHERMIND"
BUILDKIT=1 docker build -t nethermind:etb -f nethermind.Dockerfile .
