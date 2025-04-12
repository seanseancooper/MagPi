import threading

from src.config import readConfig
from src.net.rabbitMQ.RabbitMQProducer import RabbitMQProducer
from src.net.imageZMQ.ImageZMQAsyncProducer import ImageZMQAsyncProducer

import logging

logger_root = logging.getLogger('root')
arx_logger = logging.getLogger('arx_logger')


class ARXMQProvider(threading.Thread):

    def __init__(self):
        super().__init__()
        self.config = {}
        self.rmq = None
        self.zmq = None
        self.DEBUG = False

    def configure(self, config_file):
        readConfig(config_file, self.config)

        self.rmq = RabbitMQProducer(self.config['arx_queue'])
        self.zmq = ImageZMQAsyncProducer()
        self.DEBUG = self.config.get('DEBUG')

    def send_frame(self,frame):
        self.zmq.send_frame(frame)

    def send_msg(self, message):
        self.rmq.publish_message(message)

    def send_sgnlpt(self, sgnlpt):
        message = sgnlpt.get()
        self.send_frame(message.pop("audio_data"))
        self.send_msg(message)
