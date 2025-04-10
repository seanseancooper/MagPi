from datetime import datetime
import threading

from src.trx.MQTRXProducer import MQTRXProducer

from src.config import readConfig
from src.net.RabbitMQAsyncConsumer import RabbitMQAsyncConsumer

import logging

from src.trx.TRXWorker import TRXWorker

logger_root = logging.getLogger('root')
trx_logger = logging.getLogger('trx_logger')


class MQTRXRetriever(threading.Thread):
    """ MQ TRX Retriever class """
    def __init__(self):
        super().__init__()

        self.config = {}
        self.interface = None
        self.workers = []
        self.tracked_signals = {}

        self.scanner = None  # make configurable
        self.consumer = None  # make configurable

        self.device = None
        self.rate = 115200
        self.parity = None
        self.bytesize = 8
        self.stopbits = 1

        self.stats = {}                         # new, not yet used
        self.parsed_signals = []                # signals represented as a list of dictionaries.

        self.DEBUG = False

    def configure(self, config_file):
        readConfig(config_file, self.config)
        self.device = self.config['DEVICE']
        self.rate = self.config['RATE']
        self.parity = eval(self.config['PARITY'])
        self.bytesize = eval(self.config['BYTESIZE'])
        self.stopbits = eval(self.config['STOPBITS'])

        for freq in self.tracked_signals.keys():
            worker = TRXWorker(freq)
            self.config_worker(worker)
            self.workers.append(worker)

        self.DEBUG = self.config.get('DEBUG')

        self.start_scanner()
        self.start_consumer()

    def config_worker(self, worker):
        worker.retriever = self
        worker.config = self.config
        worker.created = datetime.now()
        worker.DEBUG = self.config.get('DEBUG', False)
        worker.cache_max = max(
            int(self.config.get('SIGNAL_CACHE_LOG_MAX', -5)),
            -self.config.get('SIGNAL_CACHE_MAX', 150)
        )

    def start_scanner(self):
        self.scanner = MQTRXProducer()
        self.scanner.configure('net.json')
        t = threading.Thread(target=self.scanner.run, daemon=True)
        t.start()

    def start_consumer(self):
        self.consumer = RabbitMQAsyncConsumer('trx_queue')  # make configurable
        t = threading.Thread(target=self.consumer.run, daemon=True)
        t.start()

    def scan_trx(self):
        """ scan trx interface"""
        trx_logger.info('MQ TRX retriever started')
        try:
            return self.consumer.data or []
        except Exception as e:
            trx_logger.error(f"[{__name__}]: Exception: {e}")
