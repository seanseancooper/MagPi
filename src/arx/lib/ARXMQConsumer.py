import asyncio
import threading

from src.config import readConfig
from src.net.rabbitMQ.RabbitMQConsumer import RabbitMQConsumer
from src.net.zeroMQ.ZeroMQAsyncConsumer import ZeroMQAsyncConsumer

import logging

logger_root = logging.getLogger('root')
arx_logger = logging.getLogger('arx_logger')


class ARXMQConsumer():

    def __init__(self):
        super().__init__()
        self.config = {}
        self.rmq = None
        self.zmq = None
        self.DEBUG = False

    def configure(self, config_file):
        readConfig(config_file, self.config)
        self.DEBUG = self.config.get('DEBUG')

    def get_data(self):
        return self.zmq.get_data()

    def get_metadata(self):
        return self.zmq.get_metadata()

    # def get_object(self):
    #     return self.rmq._data

    def consume_frame(self):
        self.zmq = ZeroMQAsyncConsumer()
        asyncio.run(self.zmq.receive_data())

    def consume_msg(self):
        self.rmq = RabbitMQConsumer(self.config['arx_queue'])
        t = threading.Thread(target=self.rmq.run)
        t.start()

