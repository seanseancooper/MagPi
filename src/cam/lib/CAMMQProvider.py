import threading

from src.config import readConfig
from src.net.rabbitMQ.RabbitMQProducer import RabbitMQProducer
from src.net.imageZMQ.ImageZMQAsyncProducer import ImageZMQAsyncProducer

import logging

arx_logger = logging.getLogger('arx_logger')


class CAMMQProvider(threading.Thread):

    def __init__(self):
        super().__init__()
        self.config = {}
        self.rmq = None
        self.imq = ImageZMQAsyncProducer()  # FRAMEOBJEKT_FRAME_QUEUE
        self.DEBUG = False

    def configure(self, config_file):
        readConfig(config_file, self.config)
        self.rmq = RabbitMQProducer(self.config['FRAMEOBJEKT_MESSAGE_QUEUE'])
        self.DEBUG = self.config.get('DEBUG')
        print('configured provider.')

    def send_frame(self, frame):
        self.imq.send_frame(frame)

    def send_message(self, message):
        self.rmq.publish_message(message)

    def send_frameobjekt(self, frameobjekt):
        try:
            message = frameobjekt.get()
            metadata = message['text_attributes'] # iterate
            data = frameobjekt.wall # wall ia numpy array
            frame = metadata, data

            print(f'sending zmq')
            self.send_frame(frame)

            print(f'sending rmq')
            self.send_message(message)

        except Exception as e:
            print(f'{e}')

        print(f'arxs sent!')