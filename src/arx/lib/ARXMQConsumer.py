import threading

from src.config import readConfig
from src.net.rabbitMQ.RabbitMQConsumer import RabbitMQConsumer
from src.net.imageZMQ.ImageZMQAsyncConsumer import ImageZMQAsyncConsumer

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

    def get_frame(self):
        self.zmq = ImageZMQAsyncConsumer()
        t = threading.Thread(target=self.zmq.receive_frame())
        t.start()

    def get_msg(self):
        self.rmq = RabbitMQConsumer(self.config['arx_queue'])
        t = threading.Thread(target=self.rmq.run)
        t.start()

