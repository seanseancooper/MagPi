import json
import logging
from imagezmq import ImageSender
from src.cam.lib.FrameObjekt import FrameObjekt

logger_root = logging.getLogger('logger_root')

class ImageZMQAsyncProducer:
    """ Transport FrameObjekt in the CAM module """

    def __init__(self, host, port):
        self.sender = ImageSender(connect_to=f'tcp://{host}:{port}')

    def send_frame(self, frame):
        metadata, f = frame
        logger_root.info(f"Sending: {metadata['f_id']}")
        # self.sender.send_image(json.dumps(metadata), f)

if __name__ == "__main__":
    import threading

    class CapsVid(threading.Thread):

        def __init__(self):
            super().__init__()

        def snap(self):
            import cv2 as cv
            capture = cv.VideoCapture(0)
            while capture.isOpened():
                _, frame = capture.retrieve()
                return frame

    t_host = '127.0.0.1'
    t_port = '5555'
    producer = ImageZMQAsyncProducer(t_host, t_port)

    capture = CapsVid()
    frame = capture.snap()
    while True:
        frame_objekt = FrameObjekt.create(f_id=0)
        frame_objekt.wall = frame
        producer.send_frame(frame_objekt)
