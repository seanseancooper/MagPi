import threading
from datetime import datetime, timedelta
from src.net.lib.net_utils import get_retriever
from src.config import readConfig
from src.net.zeroMQ.ZeroMQAsyncConsumer import ZeroMQAsyncConsumer
from src.net.zeroMQ.ZeroMQAsyncProducer import ZeroMQAsyncProducer

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

        self.consumer = None
        self.scanner = None                     # want to use retriever methods

        self.stats = {}                         # new, not yet used
        self.parsed_cells = []                  # a list of 'cells' representing signals as dictionaries.

        self.DEBUG = False

    def configure(self, config_file):
        readConfig(config_file, self.config)  # module config 'wifi.json'

        self.DEBUG = self.config.get('DEBUG')

        self.consumer = ZeroMQAsyncConsumer()
        self.start_scanner()
        self.start_consumer()         # can't start later... it would 'miss' signal

    # @staticmethod
    def start_scanner(self):
        self.scanner = ZeroMQWifiScanner()
        self.scanner.configure('wifi.json') # passing 'wifi', but reading 'net'!
        t = threading.Thread(target=self.scanner.run, daemon=True)
        t.start()

    def start_consumer(self):
        import asyncio
        asyncio.run(self.consumer.receive_data())

    def scan(self):
        """ called by Scanner to get scan data """
        try:
            # get data from MQ...
            scanned = self.consumer.metadata['scanned']
            return scanned or []
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
        self.producer = None

    def configure(self, config_file):
        readConfig(config_file, self.config)

        golden_retriever = get_retriever(self.config['MODULE_RETRIEVER'])
        self.mq_wifi_retriever = golden_retriever()
        self.mq_wifi_retriever.configure(config_file)
        self.producer = ZeroMQAsyncProducer()

    def parse_signals(self, readlines):
        self.parsed_signals = self.mq_wifi_retriever.get_parsed_cells(readlines)

    def run(self):

        self.created = datetime.now()
        if self.config['SPEECH_ENABLED']:
           speech_logger.info('Zero MQ WiFi scanner started')

        while True:
            scanned = self.mq_wifi_retriever.scan()
            if len(scanned) > 0:

                metadata = {
                    "id": 0,
                    "scanned": scanned
                }

                import numpy as np
                data = np.zeros((1024, 2), dtype=np.float64)
                metadata['sent'] = str(datetime.now())
                metadata["frame_shape"] = data.shape
                metadata['dtype'] = str(data.dtype)

                self.producer.send_data(metadata, data)
