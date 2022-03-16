import json
from ruamel import yaml
from web3.auto import w3

w3.eth.account.enable_unaudited_hdwallet_features


class GethKeystore(object):
    def __init__(self, config_path):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f.read())

        self.mnemonic = self.config["accounts"]["eth1-account-mnemonic"]
        self.passphrase = self.config["accounts"]["eth1-passphrase"]
        self.premines = self.config["accounts"]["eth1-premine"]

    def get_keys(self):
        keys = {}
        for acc in self.premines:
            acct = w3.eth.account.from_mnemonic(
                self.mnemonic, account_path=acc, passphrase=self.passphrase
            )
            pub = acct.address
            priv = acct.privateKey.hex()
            keys[pub] = priv
        return keys
