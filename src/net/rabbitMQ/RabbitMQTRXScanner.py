import threading
from datetime import datetime, timedelta
from src.config import readConfig
from src.net.rabbitMQ.RabbitMQProducer import RabbitMQProducer
from src.trx.TRXWorker import TRXWorker

import logging


logger_root = logging.getLogger('root')
trx_logger = logging.getLogger('trx_logger')
speech_logger = logging.getLogger('speech_logger')


class RabbitMQTRXScanner(threading.Thread):
    """ MQTRXProducer class; poll the serial/USB for signals. """
    def __init__(self):
        super().__init__()

        self.config = {}

        self.worker_id = 'RabbitMQTRXProducer'

        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()              # elapsed time since created
        self.workers = []
        self.tracked_signals = {}

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
            trx_logger.fatal(f'no retriever found {e}')
            exit(1)

    def configure(self, config_file):
        readConfig(config_file, self.config)

        golden_retriever = self.get_retriever(self.config['MQ_TRX_RETRIEVER'])
        self.retriever = golden_retriever()
        self.retriever.configure(config_file)

        for freq in self.tracked_signals.keys():
            worker = TRXWorker(freq)
            self.config_worker(worker)
            self.workers.append(worker)

        self.producer = RabbitMQProducer(self.config['MQ_TRX_QUEUE'])

    def config_worker(self, worker):
        worker.retriever = self
        worker.config = self.config
        worker.created = datetime.now()
        worker.DEBUG = self.config.get('DEBUG', False)
        worker.cache_max = max(
            int(self.config.get('SIGNAL_CACHE_LOG_MAX', -5)),
            -self.config.get('SIGNAL_CACHE_MAX', 150)
        )

    def run(self):

        self.created = datetime.now()
        speech_logger.info('MQ TRX scanner started')

        while True:
            scanned = self.retriever.scan()
            if scanned:
                self.producer.publish_message(scanned)

if __name__ == '__main__':
    scanner = RabbitMQTRXScanner()
    scanner.configure('net.json')
    scanner.run()
