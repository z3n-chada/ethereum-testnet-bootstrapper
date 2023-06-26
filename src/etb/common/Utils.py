"""
    Various utility functions that are used throughout common applications.
"""
import logging
from web3.auto import w3

logging_levels: dict = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


def get_logger(log_level: str, name: str,
               format_str: str = "%(asctime)s [%(levelname)s] %(message)s") -> logging.Logger:
    """
    Returns a logger with the given log level and name.
    @param log_level: The log level to use.
    @param name: The name of the logger.
    @param format_str: The format of the logger (default: "%(asctime)s %(levelname)s %(message)s").
    @return: The logger.
    """

    if log_level not in logging_levels:
        raise Exception(f"Unknown log level: {log_level}")
    logging.basicConfig(format=format_str)
    logger = logging.getLogger(name)
    logger.setLevel(logging_levels[log_level])
    return logger


class PremineKey(object):
    """
    Class that represents a premine key.
    These keys are present in the etb-config file via testnet-config -> execution-layer:
    account-mnemonic: the account mnemonic to use
    premines:
        account: preseed amount

    e.g.
    testnet-config:
        execution-layer:
            account-mnemonic: "cat swing flag economy stadium alone churn speed unique patch report train"
            keystore-passphrase: "testnet-password"  # passphrase for any keystore files.
            premines:
              "m/44'/60'/0'/0/0": 100000000
              "m/44'/60'/0'/0/1": 100000000
              "m/44'/60'/0'/0/2": 100000000
              "m/44'/60'/0'/0/3": 100000000

    """
    def __init__(self, mnemonic: str, account: str, passphrase: str):
        self.mnemonic: str = mnemonic
        self.account: str = account
        self.passphrase: str = passphrase
        w3.eth.account.enable_unaudited_hdwallet_features()
        acct = w3.eth.account.from_mnemonic(mnemonic, account_path=self.account, passphrase=passphrase)
        self.public_key: str = acct.address
        self.private_key = acct.key.hex()

