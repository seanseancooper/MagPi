import asyncio
import threading

from src.config import readConfig
from src.net.rabbitMQ.RabbitMQAsyncConsumer import RabbitMQAsyncConsumer
from src.net.zeroMQ.ZeroMQAsyncConsumer import ZeroMQAsyncConsumer

import logging

logger_root = logging.getLogger('root')
arx_logger = logging.getLogger('arx_logger')


class ARXMQConsumer(threading.Thread):

    def __init__(self):
        super().__init__()
        self.config = {}
        self.rmq = None
        self.zmq = ZeroMQAsyncConsumer()
        self.DEBUG = False

    def configure(self, config_file):
        readConfig(config_file, self.config)
        # self.rmq = RabbitMQAsyncConsumer(self.config['QUEUE_NAME'])
        self.DEBUG = self.config.get('DEBUG')

    def get_data(self):
        return self.zmq.get_data()

    def get_metadata(self):
        return self.zmq.get_metadata()

    def get_frame(self):
        frame = self.get_metadata(), self.get_data(),
        return frame

    def get_message(self):
        return self.rmq.data

    def consume(self):
        self.consume_zmq()
        # self.consume_rmq()

    def consume_zmq(self):
        try:
            # asyncio.run(self.zmq.receive_data())
            self.zmq.receive_data()
        except Exception as e:
            print(f'{e}')

    def consume_rmq(self):
        try:
            t = threading.Thread(target=self.rmq.run)
            t.start()
        except Exception as e:
            print(f'{e}')

