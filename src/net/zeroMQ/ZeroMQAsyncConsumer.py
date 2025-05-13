import threading
from datetime import datetime

import zmq
import numpy as np
import json
import logging
net_logger = logging.getLogger('net_logger')

class ZeroMQAsyncConsumer:
    """
    Consume ARXSignalPoint audio data for offline processing.
    ZeroMQ Consumer: consume a 'message' composed of:
            metadata: a mapping of 'text_attributes' sent [utf-8].
            data: byte array of data sent
    """
    def __init__(self):
        context = zmq.Context()

        self.socket = context.socket(zmq.SUB)  # this is hardcoded
        self.socket.connect("tcp://127.0.0.1:5555")
        self.socket.setsockopt_string(zmq.SUBSCRIBE, '')

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
        # self.metadata['time_diff'] = (datetime.now() - datetime.strptime(self.metadata['sent'], "%Y-%m-%d %H:%M:%S.%f")).total_seconds()

        # do something with data & text_attributes
        print(f'Received metadata :{self.metadata}')
        print(f'Received audio_data :{self.metadata["id"]}')

    def get_message(self):
        return self.message

    def get_metadata(self):
        return self.metadata

    def get_data(self):
        return self.data

if __name__ == "__main__":
    consumer = ZeroMQAsyncConsumer()
    while True:
        consumer.receive_data()
