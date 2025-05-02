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

        self.socket = context.socket(zmq.PULL)  # this is hardcoded
        self.socket.bind("tcp://127.0.0.1:5555")

        self.message = None     # entire message
        self.metadata = None    # encapsulates 'text_attributes'
        self.data = None        # data as utf-8 decoded bytes.

    async def receive_data(self):
        while True:
            self.message = self.socket.recv()
            metadata_part, audiodata_part = self.message.split(b'||', 1)
            self.metadata = json.loads(metadata_part.decode('utf-8'))

            shape = self.metadata['frame_shape']

            self.data = np.frombuffer(audiodata_part, dtype=np.float64).reshape(shape)
            self.metadata['time_diff'] = (datetime.now() - datetime.strptime(self.metadata['sent'], "%Y-%m-%d %H:%M:%S.%f")).total_seconds()

            # do something with ARX data & text_attributes
            net_logger.debug(f'Received metadata :{self.metadata}')
            # print(f'Received audio_data :{self.data}')

    def get_message(self):
        return self.message

    def get_metadata(self):
        return self.metadata

    def get_data(self):
        return self.data

if __name__ == "__main__":
    consumer = ZeroMQAsyncConsumer()

    import asyncio
    asyncio.run(consumer.receive_data())
