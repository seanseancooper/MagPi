import threading
from datetime import datetime, timedelta
from contextlib import contextmanager
from src.config import readConfig

import logging

from src.net.rabbitMQ.RabbitMQProducer import RabbitMQProducer

logger_root = logging.getLogger('root')
wifi_logger = logging.getLogger('wifi_logger')
speech_logger = logging.getLogger('speech_logger')


class RabbitMQWifiScanner(threading.Thread):

    """ Wifi Scanner class; poll the wifi, match BSSID and report as parsed_signals. """
    def __init__(self):
        super().__init__()

        self.config = {}
        self.retriever = None

        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()              # elapsed time since created
        self.parsed_signals = []

        self.producer = None

    @staticmethod
    def get_retriever(name):

        try:
            components = name.split('.')
            mod = __import__(components[0])
            for comp in components[1:]:
                mod = getattr(mod, comp)
            return mod
        except AttributeError as e:
            wifi_logger.fatal(f'no retriever found {e}')
            exit(1)

    def configure(self, config_file):
        readConfig(config_file, self.config)

        golden_retriever = self.get_retriever("retrievers." + self.config['WIFI_RETRIEVER'])
        self.retriever = golden_retriever()
        self.retriever.configure(config_file)

        self.producer = RabbitMQProducer(self.config['WIFI_QUEUE'])

    def parse_signals(self, readlines):
        self.parsed_signals = self.retriever.get_parsed_cells(readlines)

    @contextmanager
    def run(self):

        self.created = datetime.now()
        speech_logger.info('MQ WiFi scanner started')

        while True:
            scanned = self.retriever.scan()
            if len(scanned) > 0:
                self.producer.publish_message(scanned)

if __name__ == '__main__':
    scanner = RabbitMQWifiScanner()
    scanner.configure('wifi.json')
    scanner.run()
