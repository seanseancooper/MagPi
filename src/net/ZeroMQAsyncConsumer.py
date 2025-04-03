import json
import logging
import zmq
import numpy as np
from src.cam.Showxating.lib.FrameObjekt import FrameObjekt
from datetime import datetime

logging.basicConfig(level=logging.INFO)

class AsyncConsumer:
    def __init__(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.PULL)
        self.socket.bind("tcp://127.0.0.1:5555")

    async def receive_frame(self):
        while True:
            message = self.socket.recv()
            metadata_part, frame_part = message.split(b'||', 1)
            metadata = json.loads(metadata_part.decode('utf-8'))
            frame = np.frombuffer(frame_part, dtype=np.uint8).reshape(metadata['shape'])

            frame_objekt = FrameObjekt.create(metadata['f_id'])
            frame_objekt.wall = frame

            created_time = datetime.fromisoformat(metadata['created'])
            time_diff = (datetime.now() - created_time).total_seconds()

            logging.info(f"Received {metadata['f_id']} {metadata['created']}, time_diff={time_diff:.6f}s")

if __name__ == "__main__":
    import asyncio
    consumer = AsyncConsumer()
    asyncio.run(consumer.receive_frame())
