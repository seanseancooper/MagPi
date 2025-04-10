import json
import logging
from imagezmq import ImageHub
from src.cam.Showxating.lib.FrameObjekt import FrameObjekt
from datetime import datetime

from src.cam.Showxating.lib.FrameObjektEncoder import FrameObjektEncoder

logging.basicConfig(level=logging.INFO)

class Consumer:
    def __init__(self):
        self.hub = ImageHub(open_port="tcp://*:5555")

    def receive_frame(self):
        while True:
            metadata_json, frame = self.hub.recv_image()
            metadata = json.loads(metadata_json)

            frame_objekt = FrameObjekt.create(metadata['f_id'])
            frame_objekt.wall = frame

            # Start encoder thread to process frame
            encoder = FrameObjektEncoder(frame_objekt)
            encoder.start()

            created_time = datetime.fromisoformat(metadata['created'])
            time_diff = (datetime.now() - created_time).total_seconds()

            logging.info(f"Received {metadata['f_id']}, time_diff={time_diff:.6f}s")
            self.hub.send_reply(b"OK")

if __name__ == "__main__":
    consumer = Consumer()
    consumer.receive_frame()
