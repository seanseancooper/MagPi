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
        # self.rmq = RabbitMQProducer(self.config['QUEUE_NAME'])
        self.DEBUG = self.config.get('DEBUG')
        print('configured provider.')

    def send_frame(self, frame):
        metadata, data = frame
        self.zmq.send_data(metadata, data)  # RuntimeWarning: coroutine 'ZeroMQAsyncProducer.send_data' was never awaited

    def send_message(self, message):
        self.rmq.publish_message(message)

    def send_sgnlpt(self, arxs):
        try:
            message = arxs.get()
            metadata = message['text_attributes']
            data = arxs.get_audio_data()
            frame = metadata, data

            print(f'sending zmq')
            self.send_frame(frame)

            # print(f'sending rmq....')
            # self.send_message(message)

        except Exception as e:
            print(f'{e}')

        print(f'arxs sent!')