import threading

from src.config import readConfig
from src.net.lib.net_utils import check_rmq_available
from src.net.rabbitMQ.RabbitMQAsyncConsumer import RabbitMQAsyncConsumer

import logging

logger_root = logging.getLogger('root')
view_logger = logging.getLogger('view_logger')


class MQAggregator(threading.Thread):
    """ ViewController MQ data retriever """

    def __init__(self):
        super().__init__()
        self.config = {}
        self.consumer = None
        self.DEBUG = False

    def configure(self, config_file):
        readConfig(config_file, self.config)
        self.DEBUG = self.config.get('DEBUG')

        _ , RMQ_AVAIL = check_rmq_available(self.config['MODULE'])

        if RMQ_AVAIL:
            self.consumer = RabbitMQAsyncConsumer(self.config['AGGREGATOR_DATA_QUEUE'])
            self.start_consumer()

    def start_consumer(self):
        t = threading.Thread(target=self.consumer.run, daemon=True)
        t.start()

    def aggregate(self):
        """ aggregated data from MQ """
        try:
            if self.consumer:
                return self.consumer.data
            else:
                return []
        except Exception as e:
            view_logger.error(f"[{__name__}]: Exception: {e}")


