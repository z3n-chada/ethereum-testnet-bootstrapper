import subprocess

from .ETBConfig import ETBConfig


class Ethereal(object):
    """
    Wrapper for ethereal for various operations.
    """

    def __init__(self, etb_config: ETBConfig):
        self.etb_config = etb_config

    def beacon_deposit(self, depositdata_path, eth1_connection, eth1_pub, eth1_priv, wait=True):
        """
        submit a deposit to the beacon deposit contract
        :param depositdata_path: path to the deposit data
        :param eth1_connection: connection to ethereum client
        :param wait: if we should wait for the tx to finish
        :return:
        """
        cmd = [
            'ethereal',
            'beacon',
            'deposit',
            '--allow-duplicate-deposit',
            '--allow-excessive-deposit',
            '--allow-new-data',
            '--allow-old-data',
            '--allow-unknown-contract',
            '--connection',
            eth1_connection,
            '--data',
            str(depositdata_path),
            '--chainid',
            f"0x{self.etb_config.get('chain-id'):08x}",
            '--address',
            self.etb_config.get('deposit-contract-address'),
            '--from',
            eth1_pub,
            '--privatekey',
            eth1_priv

        ]
        if wait:
            cmd.append('--wait')
        out = subprocess.run(cmd, capture_output=True)
        if len(out.stderr) > 0:
            raise Exception(f"Exception on account create {out.stderr}")

        return out.stdout
