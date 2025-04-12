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
        self.rmq = RabbitMQProducer(self.config['QUEUE_NAME'])
        self.DEBUG = self.config.get('DEBUG')

    async def send_frame(self, frame):
        metadata, data = frame
        # print(f'sending zmq frame... {metadata}')
        await self.zmq.send_data(metadata, data)

    def send_message(self, message):
        self.rmq.publish_message(message)

    async def send_sgnlpt(self, arxs):
        message = arxs.get()

        metadata = message['text_attributes']
        # data = message.pop('audio_data')
        data = arxs.get_audio_data()
        frame = metadata, data
        # print(f'sending zmq {data}....')
        await self.send_frame(frame)
        # print(f'sending rmq....')
        self.send_message(message)
        # print(f'sent rmq....')