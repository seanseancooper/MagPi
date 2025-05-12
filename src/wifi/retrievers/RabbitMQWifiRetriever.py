import threading
from datetime import datetime, timedelta
from src.net.lib.net_utils import get_retriever, check_rmq_available
from src.config import readConfig
from src.net.rabbitMQ.RabbitMQAsyncConsumer import RabbitMQAsyncConsumer
from src.net.rabbitMQ.RabbitMQProducer import RabbitMQProducer

import logging

logger_root = logging.getLogger('root')
wifi_logger = logging.getLogger('wifi_logger')
speech_logger = logging.getLogger('speech_logger')


class RabbitMQWifiRetriever(threading.Thread):
    """ MQ Wifi Retriever class """
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
        _ , RMQ_AVAIL = check_rmq_available(self.config['MODULE'])

        if RMQ_AVAIL:
            self.consumer = RabbitMQAsyncConsumer(self.config['WIFI_QUEUE'])
            self.start_consumer()
        else:
            exit(0)

        self.start_scanner()

    # @staticmethod
    def start_scanner(self):
        self.scanner = RabbitMQWifiScanner()
        self.scanner.configure('wifi.json') # passing 'wifi', but reading 'net'!
        t = threading.Thread(target=self.scanner.run, daemon=True)
        t.start()

    def start_consumer(self):
        t = threading.Thread(target=self.consumer.run, daemon=True)
        t.start()

    def scan(self):
        """ get scan data from MQ """
        try:
            return self.consumer.data or []
        except Exception as e:
            wifi_logger.error(f"[{__name__}]: Exception: {e}")

    def get_parsed_cells(self, airport_data): # a facåde to the actual method in the thing retrieving.
        return self.scanner.mq_wifi_retriever.get_parsed_cells(airport_data)

class RabbitMQWifiScanner(threading.Thread):

    """ RabbitMQWifiScanner: use a wifi retriever to scan wifi, publish XML as lines to RabbitMQ. """
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
        readConfig('net.json', self.config) # was passed 'wifi'!

        _ , RMQ_AVAIL = check_rmq_available(self.config['MODULE'])

        if RMQ_AVAIL:
            golden_retriever = get_retriever(self.config['MQ_WIFI_RETRIEVER'])
            self.mq_wifi_retriever = golden_retriever()
            self.mq_wifi_retriever.configure(config_file) # passing 'net'
            self.producer = RabbitMQProducer(self.config['MQ_WIFI_QUEUE'])
        else:
            exit(0)

    def parse_signals(self, readlines):
        self.parsed_signals = self.mq_wifi_retriever.get_parsed_cells(readlines)

    def run(self):

        self.created = datetime.now()
        if self.config['SPEECH_ENABLED']:
           speech_logger.info('MQ WiFi scanner started')

        while True:
            scanned = self.mq_wifi_retriever.scan()
            if len(scanned) > 0:
                self.producer.publish_message(scanned)
