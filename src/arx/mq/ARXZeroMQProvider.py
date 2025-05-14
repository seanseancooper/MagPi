import threading
import asyncio
from src.config import readConfig
from src.net.zeroMQ.ZeroMQAsyncProducer import ZeroMQAsyncProducer
from src.net.zeroMQ.ZeroMQAsyncConsumer import ZeroMQAsyncConsumer

import logging

arx_logger = logging.getLogger('arx_logger')


class ARXMQProvider(threading.Thread):

    def __init__(self):
        super().__init__()
        self.config = {}
        self.producer = ZeroMQAsyncProducer()
        self.DEBUG = False

    def configure(self, config_file):
        readConfig(config_file, self.config)
        self.DEBUG = self.config.get('DEBUG')

    def send_frame(self, frame):
        metadata, data = frame
        self.producer.send_data(metadata, data)

    def send_sgnlpt(self, arxs):
        try:
            text_attributes = arxs.get()

            metadata = text_attributes['text_attributes']
            data = arxs.get_audio_data()
            frame = metadata, data

            self.send_frame(frame)

        except Exception as e:
            print(f'Exception passing signalpoint: {e}')

class ARXMQConsumer(threading.Thread):
    """ To be used by ARXEEncoder """

    def __init__(self):
        super().__init__()
        self.config = {}
        self.consumer = ZeroMQAsyncConsumer()
        self.DEBUG = False

    def configure(self, config_file):
        readConfig(config_file, self.config)
        self.DEBUG = self.config.get('DEBUG')

    def get_data(self):
        return self.consumer.data

    def get_metadata(self):
        return self.consumer.metadata

    def get_frame(self):
        frame = self.get_metadata(), self.get_data(),
        return frame

    def consume_zmq(self):
        try:
            self.consumer.receive_data()
        except Exception as e: # don't trap here
            print(f'NET::ZMQ Error {e}')
