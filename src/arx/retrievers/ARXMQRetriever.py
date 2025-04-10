import threading

from src.config import readConfig
from src.net.RabbitMQAsyncConsumer import RabbitMQAsyncConsumer
from src.arx.MQARXHelper import MQARXHelper

import logging

logger_root = logging.getLogger('root')
wifi_logger = logging.getLogger('wifi_logger')


class ARXMQRetriever(threading.Thread):
    """ MQ Wifi Retriever class """
    def __init__(self):
        super().__init__()

        self.config = {}
        self.interface = None

        self.consumer = RabbitMQAsyncConsumer('arx_queue')  # make configurablev

        self.stats = {}                         # new, not yet used
        self.parsed_signals = []                # signals represented as a list of dictionaries.
        self.DEBUG = False

    def configure(self, config_file):
        readConfig(config_file, self.config)
        self.DEBUG = self.config.get('DEBUG')

        self.start_helper()
        self.start_consumer()

    @staticmethod
    def start_helper():
        h = MQARXHelper()
        h.configure('net.json')
        t = threading.Thread(target=h.run, daemon=True)
        t.start()

    def start_consumer(self):
        t = threading.Thread(target=self.consumer.run, daemon=True)
        t.start()
