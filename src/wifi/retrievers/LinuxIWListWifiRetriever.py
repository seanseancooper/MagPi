import subprocess
import threading

from src.wifi.lib.wifi_utils import get_vendor, get_timing

from src.wifi.lib.iw_parse import get_parsed_cells, get_name, get_quality, get_channel, get_frequency, \
    get_encryption, get_address, get_signal_level, get_noise_level, get_bit_rates, get_mode

from src.config import readConfig
import logging

logger_root = logging.getLogger('root')
wifi_logger = logging.getLogger('wifi_logger')


class LinuxIWListWifiRetriever(threading.Thread):
    """ Linux specific Wifi Retriever class """
    def __init__(self):
        super().__init__()

        self.config = {}
        self.interface = None

        self.stats = {}                         # new, not yet used
        self.parsed_signals = []                # signals represented as a list of dictionaries.

        self.DEBUG = False

    def scan(self):
        """ scan configured wifi interface using iwlist """
        # TODO: mock this with a file
        try:
            process = subprocess.Popen(['iwlist', self.config['LINUX_IWLIST_MODULE_RETRIEVER_INTERFACE'], 'scan'],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       universal_newlines=True)
            return process.stdout.readlines()

        except Exception as e:
            wifi_logger.error(f"[{__name__}]: Exception: {e}")

    def configure(self, config_file):
        readConfig(config_file, self.config)
        self.DEBUG = self.config.get('DEBUG')

    def parse_signals(self, readlines):
        """ parse signals from iwlist """

        rules = {
            "SSID"      : get_name,
            "Quality"   : get_quality,
            "Channel"   : get_channel,
            "Frequency" : get_frequency,
            "Encryption": get_encryption,
            "BSSID"     : get_address,
            "Signal"    : get_signal_level,
            "Noise"     : get_noise_level,
            "BitRates"  : get_bit_rates,
            "Mode"      : get_mode,
            "Last"      : get_timing,
            "Vendor"    : get_vendor,
        }

        self.parsed_signals = get_parsed_cells(readlines, rules=rules)
