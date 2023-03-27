
echo "<<<<<<<<<< ANTITHESIS >>>>>>>>>> - Building GETH"
BUILDKIT=1 docker build -t geth_inst:etb -f geth_inst.Dockerfile .
echo "<<<<<<<<<< ANTITHESIS >>>>>>>>>> - Building BESU"
BUILDKIT=1 docker build -t besu:etb -f besu.Dockerfile .
echo "<<<<<<<<<< ANTITHESIS >>>>>>>>>> - Building NETHERMIND"
BUILDKIT=1 docker build -t nethermind:etb -f nethermind.Dockerfile .
