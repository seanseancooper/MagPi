import zmq
import json
import logging

class ZeroMQAsyncProducer:
    def __init__(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.PUSH)
        self.socket.connect("tcp://127.0.0.1:5555")

    async def send_data(self, metadata, data):
        message = json.dumps(metadata).encode('utf-8') + b'||' + data.tobytes()
        self.socket.send(message)

if __name__ == "__main__":
    def snap():
        import cv2 as cv
        c = cv.VideoCapture(0)
        while c.isOpened():
            _, f = c.retrieve()
            return f

    producer = ZeroMQAsyncProducer()
    f = snap()
    while True:
        objekt = object()
        objekt.metadata = {'text_attributes': {'shape': f.shape}}
        objekt.data = f

        import asyncio
        asyncio.run(producer.send_data(objekt.metadata,objekt.data))
