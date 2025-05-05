import threading

from src.config import readConfig
from src.net.rabbitMQ.RabbitMQProducer import RabbitMQProducer
from src.net.lib.net_utils import check_rmq_available
from src.net.imageZMQ.ImageZMQAsyncProducer import ImageZMQAsyncProducer

import logging

arx_logger = logging.getLogger('arx_logger')


class CAMMQProvider(threading.Thread):

    def __init__(self):
        super().__init__()
        self.config = {}
        self.rmq = None
        self.imq = None
        self.imq_host = None
        self.imq_port = None
        self.DEBUG = False

    def configure(self, config_file):
        readConfig(config_file, self.config)
        self.DEBUG = self.config.get('DEBUG')

        _, RMQ_AVAIL = check_rmq_available(self.config['MODULE'])

        if RMQ_AVAIL:
            self.rmq = RabbitMQProducer(self.config['RABBITMQ_QUEUE'])

        self.imq_host = self.config.get('IMQ_HOST')
        self.imq_port = self.config.get('IMQ_PORT')
        self.imq = ImageZMQAsyncProducer(self.imq_host, self.imq_port)

    def send_frame(self, frame):        # metadata & image arrays via ImageZMQ
        self.imq.send_frame(frame)

    def send_message(self, message):    # 'fields' via RabbitMQ
        if self.rmq:
            self.rmq.publish_message(message)

    def send_frameobjekt(self, frameobjekt):
        """ decompose a FrameObjekt into message, metadata and data """
        try:
            message = frameobjekt.get()             # fields & values

            metadata = message['text_attributes']   # text_attributes
            data = frameobjekt.wall                 # wall
            frame = metadata, data

            self.send_frame(frame)      # metadata, arrays
            self.send_message(message)  # fields & values

        except Exception as e:
            print(f'Exception: {e}')