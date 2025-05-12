import threading
from datetime import datetime, timedelta
from src.config import readConfig
from src.net.rabbitMQ.RabbitMQProducer import RabbitMQProducer
from src.net.lib.net_utils import get_retriever, check_rmq_available

import logging


logger_root = logging.getLogger('root')
net_logger = logging.getLogger('net_logger')
speech_logger = logging.getLogger('speech_logger')


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

if __name__ == '__main__':
    scanner = RabbitMQWifiScanner()
    scanner.configure('net.json')
    scanner.run()
