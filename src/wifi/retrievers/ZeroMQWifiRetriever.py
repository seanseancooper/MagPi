import threading
from datetime import datetime, timedelta
from src.net.lib.net_utils import get_retriever
from src.config import readConfig
from src.net.zeroMQ.ZeroMQSubscriber import ZeroMQSubscriber
from src.net.zeroMQ.ZeroMQPublisher import ZeroMQPublisher

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

        self.subcriber = None
        self.scanner = None                     # want to use retriever methods

        self.stats = {}                         # new, not yet used
        self.parsed_cells = []                  # a list of 'cells' representing signals as dictionaries.

        self.DEBUG = False

    def configure(self, config_file):
        readConfig(config_file, self.config)

        self.DEBUG = self.config.get('DEBUG')

        self.subcriber = ZeroMQSubscriber()

        self.start_scanner(config_file)

    def start_scanner(self, config_file):
        self.scanner = ZeroMQWifiScanner()
        self.scanner.configure(config_file)
        t = threading.Thread(target=self.scanner.run, daemon=True)
        t.start()

    def scan(self):
        """ called by 'Scanner' to get scan data """
        try:
            # get data from MQ...
            self.subcriber.receive_data()
            return self.subcriber.data['scanned'] or []
        except Exception as e:
            wifi_logger.error(f"[{__name__}]: Exception: {e}")

    def get_parsed_cells(self, airport_data): # a facåde to the actual method in the thing retrieving.
        return self.scanner.mq_wifi_retriever.get_parsed_cells(airport_data)

class ZeroMQWifiScanner(threading.Thread):

    """ ZeroMQWifiScanner: use a wifi retriever to scan wifi, publish XML as lines to RabbitMQ. """
    def __init__(self):
        super().__init__()

        self.config = {}

        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()              # elapsed time since created
        self.parsed_signals = []

        self.mq_wifi_retriever = None
        self.publisher = None

    def configure(self, config_file):
        readConfig(config_file, self.config)

        golden_retriever = get_retriever(self.config['MODULE_RETRIEVER'])
        self.mq_wifi_retriever = golden_retriever()
        self.mq_wifi_retriever.configure(config_file)
        self.publisher = ZeroMQPublisher()

    def parse_signals(self, readlines):
        self.parsed_signals = self.mq_wifi_retriever.get_parsed_cells(readlines)

    def run(self):

        self.created = datetime.now()
        if self.config['SPEECH_ENABLED']:
           speech_logger.info('Zero MQ WiFi scanner started')

        iteration = 0
        while True:
            scanned = self.mq_wifi_retriever.scan() # wifi 'MODULE_RETRIEVER'
            if len(scanned) > 0:

                data = {
                    'id': iteration,
                    'sent': str(datetime.now()),
                    "scanned": scanned,
                }

                self.publisher.send_data(data)
                iteration += 1