import threading
from datetime import datetime, timedelta
from src.config import readConfig
from src.net.rabbitMQ.RabbitMQProducer import RabbitMQProducer
from src.net.lib.net_utils import get_retriever

import logging


logger_root = logging.getLogger('root')
trx_logger = logging.getLogger('trx_logger')
speech_logger = logging.getLogger('speech_logger')


class RabbitMQTRXScanner(threading.Thread):
    """ RabbitMQTRXScanner: use a TRXRetriever to scan my TRX-1, publish mappings to RabbitMQ. """
    def __init__(self):
        super().__init__()

        self.config = {}

        self.worker_id = 'RabbitMQTRXProducer'

        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()                  # elapsed time since created

        self.workers = []
        self.tracked_signals = {}

        self.retriever = None                       # mq_trx_retriever
        self.producer = None

    def configure(self, config_file):
        readConfig(config_file, self.config)        # config from module, not net

        golden_retriever = get_retriever(self.config['MQ_TRX_RETRIEVER'])
        self.retriever = golden_retriever()
        self.retriever.configure(config_file)

        self.producer = RabbitMQProducer(self.config['MQ_TRX_QUEUE'])

    def run(self):

        self.created = datetime.now()
        if self.config['SPEECH_ENABLED']:
            speech_logger.info('MQ TRX scanner started')

        while True:
            scanned = self.retriever.scan()
            if scanned:
                self.producer.publish_message(scanned)

if __name__ == '__main__':
    scanner = RabbitMQTRXScanner()
    scanner.configure('net.json')
    scanner.run()
