import requests

class BeaconAPIManager(object):
    def __init__(self):
        self.client = {}

    def add_client(self, client):
        self.clients[client.host] = client

class BeaconAPIClient(object):
    def __init__(self, host, port, client):
        self.host = host
        self.port = port
        self.client = client

        self.current_chain = []
        self.current_justified_chain = []
        self.current_finalized_chain = []

    def __repr__(self):
        return f"{self.host}:{self.port} ({self.client})"

    def get_genesis(self):
