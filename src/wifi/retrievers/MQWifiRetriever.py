import threading

from src.net.rabbitMQ.RabbitMQWifiScanner import RabbitMQWifiScanner
from src.config import readConfig
from src.net.rabbitMQ.RabbitMQAsyncConsumer import RabbitMQAsyncConsumer

import logging

logger_root = logging.getLogger('root')
wifi_logger = logging.getLogger('wifi_logger')


class MQWifiRetriever(threading.Thread):
    """ MQ Wifi Retriever class """
    def __init__(self):
        super().__init__()

        self.config = {}
        self.interface = None

        self.consumer = RabbitMQAsyncConsumer('wifi_queue')

        self.stats = {}                         # new, not yet used
        self.parsed_signals = []                # signals represented as a list of dictionaries.

        self.DEBUG = False

    def configure(self, config_file):
        readConfig(config_file, self.config)

        self.DEBUG = self.config.get('DEBUG')

        self.start_scanner()
        self.consumer = RabbitMQAsyncConsumer(self.config['WIFI_QUEUE'])
        self.start_consumer()

    @staticmethod
    def start_scanner():
        scanner = RabbitMQWifiScanner()
        scanner.configure('wifi.json')
        t = threading.Thread(target=scanner.run, daemon=True)
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


    def get_parsed_cells(self, airport_data):
        from src.wifi.retrievers.MacOSAirportWifiRetriever import MacOSAirportWifiRetriever
        return MacOSAirportWifiRetriever.get_parsed_cells(MacOSAirportWifiRetriever(), airport_data)

