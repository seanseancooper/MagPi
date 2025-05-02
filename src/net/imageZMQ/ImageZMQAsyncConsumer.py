import json
import logging
from imagezmq import ImageHub
from src.cam.lib.FrameObjekt import FrameObjekt
from datetime import datetime

logger_root = logging.getLogger('logger_root')

class ImageZMQAsyncConsumer:
    """ Transport FrameObjekt in the CAM module """

    def __init__(self, host, port):
        self.hub = ImageHub(open_port=f'tcp://{host}:{port}')

    def receive_frame(self):
        while True:
            metadata_json, f = self.hub.recv_image()

            """ rehydrate FrameObjekt from metadata & data """
            metadata = json.loads(metadata_json)
            metadata['time_diff'] = (datetime.now() - metadata['created']).total_seconds()
            frameobjekt = FrameObjekt.dict_to_frameobjekt(metadata)
            frameobjekt.wall = f

            # Start encoder thread to process FrameObjekt
            # from src.cam.lib.FrameObjektEncoder import FrameObjektEncoder
            # encoder = FrameObjektEncoder(frame_objekt)
            # encoder.start()

            logger_root.info(f"Received {metadata}")
            self.hub.send_reply(b"OK")

if __name__ == "__main__":

    t_host = 'localhost'
    t_port = '5555'
    consumer = ImageZMQAsyncConsumer(t_host, t_port)
    consumer.receive_frame()
