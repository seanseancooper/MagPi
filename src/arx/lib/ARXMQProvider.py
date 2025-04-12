import threading

from src.config import readConfig
from src.net.rabbitMQ.RabbitMQProducer import RabbitMQProducer
from src.net.zeroMQ.ZeroMQAsyncProducer import ZeroMQAsyncProducer

import logging

arx_logger = logging.getLogger('arx_logger')


class ARXMQProvider(threading.Thread):

    def __init__(self):
        super().__init__()
        self.config = {}
        self.rmq = None
        self.zmq = ZeroMQAsyncProducer()
        self.DEBUG = False

    def configure(self, config_file):
        readConfig(config_file, self.config)
        self.rmq = RabbitMQProducer(self.config['arx_queue'])
        self.DEBUG = self.config.get('DEBUG')

    def send_frame(self, frame):
        metadata, data = frame
        self.zmq.send_data(metadata, data)

    def send_message(self, message):
        self.rmq.publish_message(message)

    def send_sgnlpt(self, sgnlpt):
        message = sgnlpt.get()

        metadata = message['text_attributes']
        data = message.pop('audio_data')
        frame = metadata, data

        self.send_frame(frame)
        self.send_message(message)
