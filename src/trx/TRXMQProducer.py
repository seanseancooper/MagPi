import threading
from datetime import datetime, timedelta
from contextlib import contextmanager
from src.config import readConfig

import logging

from src.net.rabbitMQ.RabbitMQProducer import RabbitMQProducer
from src.trx.TRXWorker import TRXWorker

logger_root = logging.getLogger('root')
trx_logger = logging.getLogger('trx_logger')
speech_logger = logging.getLogger('speech_logger')


class TRXMQProducer(threading.Thread):

    """ MQTRXProducer class; poll the serial/USB for signals. """
    def __init__(self):
        super().__init__()

        self.config = {}
        self.worker_id = 'MQTRXScanner'
        self.signal_cache = []
        self.workers = []
        self.tracked_signals = {}
        self.out = None

        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()              # elapsed time since created

        self.device = None
        self.rate = 115200
        self.parity = None
        self.bytesize = 8
        self.stopbits = 1

        self.polling_count = 0
        self.lat = 0.0
        self.lon = 0.0
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

    def config_worker(self, worker):
        worker.retriever = self
        worker.config = self.config
        worker.created = datetime.now()
        worker.DEBUG = self.config.get('DEBUG', False)
        worker.cache_max = max(
            int(self.config.get('SIGNAL_CACHE_LOG_MAX', -5)),
            -self.config.get('SIGNAL_CACHE_MAX', 150)
        )

    def configure(self, config_file):
        readConfig(config_file, self.config)

        golden_retriever = self.get_retriever("retrievers." + self.config['TRX_RETRIEVER'])
        self.retriever = golden_retriever()
        self.retriever.configure(config_file)

        self.device = self.config['DEVICE']
        self.rate = self.config['RATE']
        self.parity = self.config['PARITY']
        self.bytesize = self.config['BYTESIZE']
        self.stopbits = self.config['STOPBITS']

        for freq in self.tracked_signals.keys():
            worker = TRXWorker(freq)
            self.config_worker(worker)
            self.workers.append(worker)

        self.producer = RabbitMQProducer(self.config['TRX_QUEUE'])

    @contextmanager
    def run(self):

        self.created = datetime.now()
        trx_logger.info('MQ TRX scanner started')
        # move this to the controller:
        # t = threading.Thread(target=self.retriever.run)
        # t.start()

        while True:
            scanned = self.retriever.scan()
            if scanned:
                self.producer.publish_message(scanned)

if __name__ == '__main__':
    scanner = TRXMQProducer()
    scanner.configure('trx.json')
    scanner.run()
