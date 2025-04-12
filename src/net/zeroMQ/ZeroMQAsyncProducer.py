import cv2 as cv
import threading
import json
import logging

import zmq
from src.cam.lib.FrameObjekt import FrameObjekt

logging.basicConfig(level=logging.INFO)

class ZeroMQAsyncProducer:
    def __init__(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.PUSH)
        self.socket.connect("tcp://127.0.0.1:5555")

    async def send_frame(self, frame_objekt: FrameObjekt):

        metadata = {
            "f_id": frame_objekt.f_id,
            "created": frame_objekt.created.isoformat(),
            "shape": frame_objekt.wall.shape
        }
        message = json.dumps(metadata).encode('utf-8') + b'||' + frame_objekt.wall.tobytes()


        logging.info(f"Sending: {metadata}")
        self.socket.send(message)

class CapsVid(threading.Thread):

    def __init__(self):
        super().__init__()

    def snap(self):
        capture = cv.VideoCapture(0)
        while capture.isOpened():
            _, frame = capture.retrieve()
            return frame

if __name__ == "__main__":
    import asyncio
    producer = ZeroMQAsyncProducer()
    capture = CapsVid()
    frame = capture.snap()
    while True:
        frame_objekt = FrameObjekt.create(f_id="test_frame")
        frame_objekt.wall = frame
        asyncio.run(producer.send_frame(frame_objekt))
