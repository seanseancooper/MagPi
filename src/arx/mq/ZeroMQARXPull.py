import threading
from datetime import datetime

import zmq
import numpy as np
import json
import logging
net_logger = logging.getLogger('net_logger')

class ZeroMQARXPull:
    """
    Consume ARXSignalPoint audio data for offline processing.
    ZeroMQ Consumer: consume a 'message' composed of:
            metadata: a mapping of 'text_attributes' sent [utf-8].
            data: byte array of data sent
    """
    def __init__(self, I_ZMQ_HOST, I_ZMQ_PORT):
        self.host = I_ZMQ_HOST
        self.port = I_ZMQ_PORT
        context = zmq.Context()

        self.socket = context.socket(zmq.PULL)
        self.socket.connect(f'tcp://{self.host}:{self.port}')

        self.message = None     # entire message
        self.metadata = None    # encapsulates 'text_attributes'
        self.data = None        # data as utf-8 decoded bytes.

    def receive_data(self):

        self.message = self.socket.recv()
        metadata_part, data_part = self.message.split(b'||', 1)
        self.metadata = json.loads(metadata_part.decode('utf-8'))

        frame_shape = self.metadata['frame_shape']
        dtype = self.metadata['dtype']
        shape = tuple(int(_) for _ in frame_shape)

        self.data = np.frombuffer(data_part, dtype=dtype).reshape(shape)
        self.metadata['time_diff'] = (datetime.now() - datetime.strptime(self.metadata['sent'], "%Y-%m-%d %H:%M:%S.%f")).total_seconds()

        # do something with data & text_attributes
        net_logger.debug(f'time diff:{self.metadata["time_diff"]}')
        net_logger.info(f'Received metadata: {self.metadata}')
        net_logger.info(f'Received audio_data: {self.data}')

    def get_message(self):
        return self.message

    def get_metadata(self):
        return self.metadata

    def get_data(self):
        return self.data

if __name__ == "__main__":
    consumer = ZeroMQARXPull()
    while True:
        consumer.receive_data()
