import threading

from src.config import readConfig
from src.net.imageZMQ.ImageZMQAsyncProducer import ImageZMQAsyncProducer

import logging

arx_logger = logging.getLogger('arx_logger')


class CAMMQProvider(threading.Thread):

    def __init__(self):
        super().__init__()
        self.config = {}
        self.imq = None
        self.imq_host = None
        self.imq_port = None
        self.DEBUG = False

    def configure(self, config_file):
        readConfig(config_file, self.config)
        self.DEBUG = self.config.get('DEBUG')

        self.imq_host = self.config.get('IMQ_HOST')
        self.imq_port = self.config.get('IMQ_PORT')
        self.imq = ImageZMQAsyncProducer(self.imq_host, self.imq_port)

    def send_frame(self, frame):        # metadata & image arrays via ImageZMQ
        self.imq.send_frame(frame)

    def send_frameobjekt(self, frameobjekt):
        """ decompose a FrameObjekt into message, metadata and data """
        try:
            message = frameobjekt.get()             # fields & values

            metadata = message['text_attributes']   # text_attributes
            data = frameobjekt.wall                 # wall
            frame = metadata, data

            self.send_frame(frame)

        except Exception as e:
            print(f'Exception: {e}')