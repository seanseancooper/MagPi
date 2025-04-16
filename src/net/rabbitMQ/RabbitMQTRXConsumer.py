import threading
from datetime import datetime, timedelta
from src.config import readConfig
from src.net.rabbitMQ.RabbitMQAsyncConsumer import RabbitMQAsyncConsumer
from src.trx.TRXWorker import TRXWorker

import logging

logger_root = logging.getLogger('root')
trx_logger = logging.getLogger('trx_logger')


class RabbitMQTRXConsumer(threading.Thread):
    """ MQ TRX Retriever class """
    def __init__(self):
        super().__init__()

        self.config = {}
        self.workers = []
        self.tracked_signals = {}

        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()              # elapsed time since created

        self.retriever = None
        self.consumer = None
        self.out = None

        self.DEBUG = False

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

        golden_retriever = self.get_retriever("retrievers." + self.config['MQ_TRX_RETRIEVER'])
        self.retriever = golden_retriever()
        self.retriever.configure(config_file)

        for freq in self.tracked_signals.keys():
            worker = TRXWorker(freq)
            worker.config_worker(self)
            self.workers.append(worker)

        self.DEBUG = self.config.get('DEBUG')

        self.start_consumer()

    def start_consumer(self):
        self.consumer = RabbitMQAsyncConsumer(self.config['TRX_QUEUE'])
        t = threading.Thread(target=self.consumer.run, daemon=True)
        t.start()

    def stop(self):
        print("Retriever stopping...")

    def scan(self):
        """ scan MQ for messages """
        trx_logger.info('MQ TRX retriever started')
        try:
            return self.consumer.data or []
        except Exception as e:
            trx_logger.error(f"[{__name__}]: Exception: {e}")

if __name__ == '__main__':
    consumer = RabbitMQTRXConsumer()
    consumer.configure('net.json')
    consumer.scan()
