import threading
from src.config import readConfig
from src.arx.mq.ZeroMQARXPush import ZeroMQARXPush
from src.arx.mq.ZeroMQARXPull import ZeroMQARXPull

import logging

arx_logger = logging.getLogger('arx_logger')


class ARXMQProvider(threading.Thread):
    """ Signal processing occurs on stop() to trigger ARXSignalPoint offline processing.
    ARXMQProvider uses ZeroMQARXPush & ZeroMQARXPull to pass an ARXSignalPoint type. We
    need to wait for the entire file to be rendered as .wav before trying to process it
    with ARXEncoder. Note there is no need/opportunity for reconnection here.

    ARXMQProvider splits the ARXSignalPoint into data and metadata, then uses ARXMQProvider
    to PUSH the unit as a frame. The ZeroMQARXPull frame is reconstructed as metadata and
    data by ARXMQConsumer.
    """
    def __init__(self):
        super().__init__()
        self.config = {}
        self.push = None
        self.DEBUG = False

    def configure(self, config_file):
        readConfig(config_file, self.config)
        self.DEBUG = self.config.get('DEBUG')
        self.push = ZeroMQARXPush(self.config.get('I_ZMQ_HOST'), self.config.get('I_ZMQ_PORT'))

    def send_frame(self, frame):
        metadata, data = frame
        self.push.send_data(metadata, data)

    def send_sgnlpt(self, arxs):
        try:
            text_attributes = arxs.get()

            metadata = text_attributes['text_attributes']
            data = arxs.get_audio_data()
            frame = metadata, data

            self.send_frame(frame)

        except Exception as e:
            print(f'Exception passing signalpoint: {e}')

class ARXMQConsumer:
    """ To be used by ARXEncoder """

    def __init__(self):
        super().__init__()
        self.config = {}
        self.pull = None
        self.DEBUG = False

    def configure(self, config_file):
        readConfig(config_file, self.config)
        self.DEBUG = self.config.get('DEBUG')
        self.pull = ZeroMQARXPull(self.config.get('I_ZMQ_HOST'), self.config.get('I_ZMQ_PORT'))

    def get_data(self):
        return self.pull.data

    def get_metadata(self):
        return self.pull.metadata

    def get_frame(self):
        frame = self.get_metadata(), self.get_data(),
        return frame

    def consume_zmq(self):
        try:
            self.pull.receive_data()
        except Exception as e: # don't trap here
            print(f'NET::ZMQ Error {e}')
