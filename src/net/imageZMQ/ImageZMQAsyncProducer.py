import threading
import cv2 as cv
import json
import logging
from imagezmq import ImageSender
from src.cam.lib.FrameObjekt import FrameObjekt

logging.basicConfig(level=logging.INFO)

class ImageZMQAsyncProducer:
    def __init__(self):
        self.sender = ImageSender(connect_to="tcp://127.0.0.1:5555")

    def send_frame(self, frame_objekt: FrameObjekt):
        metadata = {
            "f_id": frame_objekt.f_id,
            "created": frame_objekt.created.isoformat(),
            "shape": frame_objekt.wall.shape
        }
        logging.info(f"Sending: {metadata}")
        self.sender.send_image(json.dumps(metadata), frame_objekt.wall)

class CapsVid(threading.Thread):

    def __init__(self):
        super().__init__()

    def snap(self):
        capture = cv.VideoCapture(0)
        while capture.isOpened():
            _, frame = capture.retrieve()
            return frame


if __name__ == "__main__":
    producer = ImageZMQAsyncProducer()
    capture = CapsVid()
    frame = capture.snap()
    while True:
        frame_objekt = FrameObjekt.create(f_id="test_frame")
        frame_objekt.wall = frame
        producer.send_frame(frame_objekt)
