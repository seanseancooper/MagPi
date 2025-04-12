import zmq
import numpy as np
import json
import logging

class ZeroMQAsyncConsumer:
    def __init__(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.PULL)
        self.socket.bind("tcp://127.0.0.1:5555")
        self._message = None    # entire message
        self._metadata = None   # ARX 'text_attributes'
        self._data = None       # ARX 'audio_data'

    async def receive_data(self):
        while True:
            self._message = self.socket.recv()
            metadata_part, data_part = self._message.split(b'||', 1)

            self._metadata = json.loads(metadata_part.decode('utf-8'))
            self._data = np.frombuffer(data_part, dtype=np.uint8).reshape(self._metadata['text_attributes']['shape'])

            logging.info(f"Received data")

    def get_message(self):
        return self._message

    def get_metadata(self):
        return self._metadata

    def get_data(self):
        return self._data

if __name__ == "__main__":
    consumer = ZeroMQAsyncConsumer()

    import asyncio
    asyncio.run(consumer.receive_data())
