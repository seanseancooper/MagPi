import json
import logging
from imagezmq import ImageHub
from src.cam.lib.FrameObjekt import FrameObjekt
from datetime import datetime
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

            metadata['time_diff'] = (datetime.now() - frameobjekt.created).total_seconds()

            print(f"Received {metadata}")
            self.hub.send_reply(b"OK")

if __name__ == "__main__":

    host = '127.0.0.1'
    port = '5555'
    consumer = ImageZMQAsyncConsumer(host, port)
    consumer.receive_frame()
