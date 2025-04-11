import threading

from src.config import readConfig
from src.net.rabbitMQ.RabbitMQAsyncProducer import RabbitMQAsyncProducer
from src.arx.ZeroMQARXHelper import ZeroMQARXHelper

import logging

logger_root = logging.getLogger('root')
wifi_logger = logging.getLogger('wifi_logger')


class ARXMQProvider(threading.Thread):
    """ MQ Wifi Retriever class """
    def __init__(self):
        super().__init__()

        self.config = {}
        self.interface = None

        self.producer = RabbitMQAsyncProducer('arx_queue')  # make configurablev
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

    def start_producer(self):
        t = threading.Thread(target=self.producer.run, daemon=True)
        t.start()
