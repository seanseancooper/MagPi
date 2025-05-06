import json
import threading
import asyncio
from src.config import readConfig
from src.net.lib.net_utils import check_rmq_available
from src.net.rabbitMQ.RabbitMQProducer import RabbitMQProducer
from src.net.rabbitMQ.RabbitMQAsyncConsumer import RabbitMQAsyncConsumer
from src.net.zeroMQ.ZeroMQAsyncProducer import ZeroMQAsyncProducer
from src.net.zeroMQ.ZeroMQAsyncConsumer import ZeroMQAsyncConsumer

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
        self.DEBUG = self.config.get('DEBUG')
        _, RMQ_AVAIL = check_rmq_available(self.config['MODULE'])

        if RMQ_AVAIL:
            self.rmq = RabbitMQProducer(self.config['ARX_QUEUE'])

    def send_frame(self, frame):
        metadata, data = frame
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.zmq.send_data(metadata, data))

    def send_message(self, message):
        self.rmq.publish_message(message)

    def send_sgnlpt(self, arxs):
        try:
            text_attributes = arxs.get()
            metadata = text_attributes['text_attributes']
            data = arxs.get_audio_data()
            frame = metadata, data

            if self.zmq:
                # print(f'sending zmq')
                self.send_frame(frame)

            if self.rmq:
                # print(f'sending rmq')
                self.send_message(json.dumps(text_attributes).encode('utf-8'))

        except Exception as e:
            print(f'{e}')

class ARXMQConsumer(threading.Thread):

    def __init__(self):
        super().__init__()
        self.config = {}
        self.rmq = None
        self.zmq = ZeroMQAsyncConsumer()
        self.DEBUG = False

    def configure(self, config_file):
        readConfig(config_file, self.config)
        self.DEBUG = self.config.get('DEBUG')
        _, RMQ_AVAIL = check_rmq_available(self.config['MODULE'])

        if RMQ_AVAIL:
            self.rmq = RabbitMQAsyncConsumer(self.config['ARX_QUEUE'])

    def get_data(self):
        return self.zmq.get_data()

    def get_metadata(self):
        return self.zmq.get_metadata()

    def get_frame(self):
        frame = self.get_metadata(), self.get_data(),
        return frame

    def get_message(self):
        return self.rmq.data if self.rmq else None

    def consume(self):
        self.consume_zmq()
        if self.rmq:
            self.consume_rmq()

    def consume_zmq(self):
        try:
            # asyncio.run(self.zmq.receive_data())
            self.zmq.receive_data()
        except Exception as e: # don't trap here
            print(f'NET::ZMQ Error {e}')

    def consume_rmq(self):
        try:
            t = threading.Thread(target=self.rmq.run)
            t.start()
        except Exception as e: # don't trap here
            print(f'NET::RMQ Error {e}')
