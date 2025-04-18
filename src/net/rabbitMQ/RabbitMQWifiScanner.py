import threading
from datetime import datetime, timedelta
from src.config import readConfig
from src.net.rabbitMQ.RabbitMQProducer import RabbitMQProducer

import logging


logger_root = logging.getLogger('root')
wifi_logger = logging.getLogger('wifi_logger')
speech_logger = logging.getLogger('speech_logger')


class RabbitMQWifiScanner(threading.Thread):

    """ Wifi Scanner class; poll the wifi, match BSSID and report as parsed_signals. """
    def __init__(self):
        super().__init__()

        self.config = {}

        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()              # elapsed time since created
        self.parsed_signals = []

        self.retriever = None
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
        readConfig('net.json', self.config)

        golden_retriever = self.get_retriever("retrievers." + self.config['MQ_WIFI_RETRIEVER'])
        self.retriever = golden_retriever()
        self.retriever.configure(config_file)

        self.producer = RabbitMQProducer(self.config['MQ_WIFI_QUEUE'])

    def parse_signals(self, readlines):
        self.parsed_signals = self.retriever.get_parsed_cells(readlines)

    def run(self):

        self.created = datetime.now()
        speech_logger.info('MQ WiFi scanner started')

        while True:
            scanned = self.retriever.scan()
            if len(scanned) > 0:
                self.producer.publish_message(scanned)

if __name__ == '__main__':
    scanner = RabbitMQWifiScanner()
    scanner.configure('net.json')
    scanner.run()
