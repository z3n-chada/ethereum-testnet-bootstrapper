from etb-client-runner:latest

workdir /usr/app 
run apt install -y --no-install-recommends python3-dev make g++
run ln -s /usr/local/bin/python3 /usr/local/bin/python
ARG VERSION=next
ENV VERSION=$VERSION
RUN npm install -g npm@8.8.0
RUN npm install @chainsafe/lodestar-cli@$VERSION

RUN ln -s /usr/app/node_modules/.bin/lodestar /usr/local/bin/lodestar

ENTRYPOINT ["/bin/bash"]
