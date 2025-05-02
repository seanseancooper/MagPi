import zmq
import json
import logging

net_logger = logging.getLogger('net_logger')

class ZeroMQAsyncProducer:
    """
    Publish ARXSignalPoint audio data to offline processing.
    ZeroMQ Producer: Produce a 'message' composed of:
            metadata: a mapping of 'text_attributes' sent [utf-8].
            data: byte array of data sent
    """
    def __init__(self):
        context = zmq.Context()

        self.socket = context.socket(zmq.PUSH)   #???!!!!!!
        self.socket.connect("tcp://127.0.0.1:5555")

    async def send_data(self, metadata, audiodata):
        message = json.dumps(metadata).encode('utf-8') + b'||' + audiodata.tobytes()
        net_logger.debug(f"Sending data. {metadata['id']}")
        self.socket.send(message)

if __name__ == "__main__":
    import asyncio
    from src.cam.lib.FrameObjekt import FrameObjekt

    def snap():
        import cv2 as cv
        c = cv.VideoCapture(0)
        while c.isOpened():
            _, f = c.retrieve()
            return f

    producer = ZeroMQAsyncProducer()
    f = snap()
    while True:

        frame_objekt = FrameObjekt.create(f_id="0")
        frame_objekt.wall = f
        frame_objekt._text_attributes = {'text_attributes': {'frame_shape': f.shape, 'dtype': f.dtype}}

        asyncio.run(producer.send_data(frame_objekt.get_text_attributes(),frame_objekt.wall))
