import threading

from src.config import readConfig
from src.net.imageZMQ.ImageZMQAsyncProducer import ImageZMQAsyncProducer
from src.net.imageZMQ.ImageZMQAsyncConsumer import ImageZMQAsyncConsumer

import logging

arx_logger = logging.getLogger('arx_logger')


class CAMMQProvider(threading.Thread):

    def __init__(self):
        super().__init__()
        self.config = {}
        self.producer = None
        # self.consumer = None
        self.DEBUG = False

    def configure(self, config_file):
        readConfig(config_file, self.config)
        self.DEBUG = self.config.get('DEBUG')
        self.producer = ImageZMQAsyncProducer(self.config.get('IMQ_HOST'),self.config.get('IMQ_PORT'))
        # self.consumer = ImageZMQAsyncConsumer(self.config.get('IMQ_HOST'),self.config.get('IMQ_PORT'))

    def send_frame(self, frame):        # metadata & image arrays via ImageZMQ
        self.producer.send_frame(frame)

    def send_frameobjekt(self, frameobjekt):
        """ decompose a FrameObjekt into message, metadata and data """
        try:
            message = frameobjekt.get()             # fields & values

            metadata = message['text_attributes']   # text_attributes
            data = frameobjekt.wall                 # wall
            frame = metadata, data

            # self.send_frame(frame)

        except Exception as e:
            print(f'Exception: {e}')