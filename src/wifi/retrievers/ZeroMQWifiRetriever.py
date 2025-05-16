import asyncio
import threading
from datetime import datetime, timedelta
from src.net.lib.net_utils import get_retriever
from src.config import readConfig
from src.net.zeroMQ.ZeroMQPull import ZeroMQPull
from src.net.zeroMQ.ZeroMQPush import ZeroMQPush

import logging

logger_root = logging.getLogger('root')
wifi_logger = logging.getLogger('wifi_logger')
speech_logger = logging.getLogger('speech_logger')


class ZeroMQWifiRetriever(threading.Thread):
    """ ZeroMQ Wifi Retriever class """
    def __init__(self):
        super().__init__()

        self.config = {}
        self.interface = None

        self.pull = None
        self.scanner = None                     # want to use retriever method

        self.stats = {}                         # new, not yet used
        self.parsed_cells = []                  # a list of 'cells' representing signals as dictionaries.

        self.DEBUG = False

    def configure(self, config_file):
        readConfig(config_file, self.config)

        self.DEBUG = self.config.get('DEBUG')

        self.pull = ZeroMQPull(self.config.get('I_ZMQ_HOST'), self.config.get('I_ZMQ_PORT'))
        self.start_scanner(config_file)

    def start_scanner(self, config_file):
        """ I/O bound process  """
        self.scanner = ZeroMQWifiScanner()
        self.scanner.configure(config_file)
        t = threading.Thread(target=self.scanner.run, daemon=True)
        t.start()

    def scan(self):
        """ called by 'Scanner' to get scan data """
        asyncio.run(self.pull.receive_data())

        try:
            # get data from MQ...
            return self.pull.data['scanned'] or []
        except Exception as e:
            wifi_logger.error(f"[{__name__}]: Exception: {e}")

    def get_parsed_cells(self, airport_data): # a facåde to the actual method in the thing retrieving.
        return self.scanner.wifi_retriever.get_parsed_cells(airport_data)

class ZeroMQWifiScanner(threading.Thread):

    """ ZeroMQWifiScanner: use a wifi retriever to scan wifi, publish XML as lines to RabbitMQ. """
    def __init__(self):
        super().__init__()

        self.config = {}
        self.iters = 0
        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()              # elapsed time since created
        self.parsed_signals = []
        self.scanned = None

        self.wifi_retriever = None
        self.push = None

    def configure(self, config_file):
        readConfig(config_file, self.config)

        module_retriever = get_retriever(self.config['MODULE_RETRIEVER'])
        self.wifi_retriever = module_retriever()
        self.wifi_retriever.configure(config_file)

        self.push = ZeroMQPush(self.config.get('I_ZMQ_HOST'), self.config.get('I_ZMQ_PORT'))

    def parse_signals(self, readlines):
        self.parsed_signals = self.wifi_retriever.get_parsed_cells(readlines)

    def run(self):

        if self.config['SPEECH_ENABLED']:
           speech_logger.info('Zero MQ WiFi scanner started')

        while True:
            # idea: I/O bound here, but I don't want to 'async' this
            self.scanned = self.wifi_retriever.scan() or ''
            if len(self.scanned) > 0:

                data = {
                    'id': self.iters,
                    'sent': str(datetime.now()),
                    "scanned": self.scanned,
                }

                self.push.send_data(data)
            self.iters += 1
