import threading
import cv2 as cv
import json
import logging
from imagezmq import ImageSender
from src.cam.lib.FrameObjekt import FrameObjekt

logging.basicConfig(level=logging.INFO)

class ImageZMQAsyncProducer:
    """ used to transport FrameObjekts and metadata """

    def __init__(self, host, port):
        self.sender = ImageSender(connect_to=f'tcp://{host}:{port}')

    def send_frame(self, frameobjekt: FrameObjekt):
        metadata = frameobjekt.frameobjekt_to_dict(frameobjekt)
        logging.debug(f"Sending: {metadata['f_id']}")
        self.sender.send_image(json.dumps(metadata), frameobjekt.wall)

if __name__ == "__main__":

    class CapsVid(threading.Thread):

        def __init__(self):
            super().__init__()

        def snap(self):
            capture = cv.VideoCapture(0)
            while capture.isOpened():
                _, frame = capture.retrieve()
                return frame

    host = '127.0.0.1'
    port = '5555'
    producer = ImageZMQAsyncProducer(host, port)

    capture = CapsVid()
    frame = capture.snap()
    while True:
        frame_objekt = FrameObjekt.create(f_id=0)
        frame_objekt.wall = frame
        producer.send_frame(frame_objekt)
