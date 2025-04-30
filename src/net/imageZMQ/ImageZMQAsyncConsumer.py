import json
import logging
from imagezmq import ImageHub
from src.cam.lib.FrameObjekt import FrameObjekt
from datetime import datetime

from src.cam.lib import FrameObjektEncoder

logging.basicConfig(level=logging.INFO)

class ImageZMQAsyncConsumer:
    """ used to transport FrameObjekts and metadata """

    def __init__(self, host, port):
        self.hub = ImageHub(open_port=f'tcp://{host}:{port}')

    def receive_frame(self):
        while True:
            metadata_json, frame = self.hub.recv_image()
            metadata = json.loads(metadata_json)
            frameobjekt = FrameObjekt.dict_to_frameobjekt(metadata)

            # # Start encoder thread to process frame
            # from src.cam.lib.FrameObjektEncoder import FrameObjektEncoder
            # encoder = FrameObjektEncoder(frame_objekt)
            # encoder.start()

            # Start encoder thread to process frame
            encoder = FrameObjektEncoder(frame_objekt)
            encoder.start()

            created_time = datetime.fromisoformat(metadata['created'])
            time_diff = (datetime.now() - created_time).total_seconds()

            logging.info(f"Received {metadata['f_id']}, time_diff={time_diff:.6f}s")
            self.hub.send_reply(b"OK")

if __name__ == "__main__":
    consumer = ImageZMQAsyncConsumer()
    consumer.receive_frame()
