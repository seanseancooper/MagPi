import threading

from src.config import readConfig
from src.net.rabbitMQ.RabbitMQProducer import RabbitMQProducer
from src.net.zeroMQ.ZeroMQAsyncProducer import ZeroMQAsyncProducer
from src.net.rabbitMQ.RabbitMQAsyncConsumer import RabbitMQAsyncConsumer
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
        self.rmq = RabbitMQProducer(self.config['ARX_QUEUE'])
        self.DEBUG = self.config.get('DEBUG')

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

            print(f'sending rmq')
            self.send_message(message)

        except Exception as e:
            print(f'{e}')

        print(f'arxs sent!')

class ARXMQConsumer(threading.Thread):

    def __init__(self):
        super().__init__()
        self.config = {}
        self.rmq = None
        self.zmq = ZeroMQAsyncConsumer()
        self.DEBUG = False

    def configure(self, config_file):
        readConfig(config_file, self.config)
        self.rmq = RabbitMQAsyncConsumer(self.config['ARX_QUEUE'])
        self.DEBUG = self.config.get('DEBUG')

    def get_data(self):
        return self.zmq.get_data()

    def get_metadata(self):
        return self.zmq.get_metadata()

    def get_frame(self):
        frame = self.get_metadata(), self.get_data(),
        return frame

    def get_message(self):
        return self.rmq.data

    def consume(self):
        # self.consume_zmq()
        self.consume_rmq()

    def consume_zmq(self):
        try:
            # asyncio.run(self.zmq.receive_data())
            self.zmq.receive_data()
        except Exception as e:
            print(f'{e}')

    def consume_rmq(self):
        try:
            t = threading.Thread(target=self.rmq.run)
            t.start()
        except Exception as e:
            print(f'{e}')

