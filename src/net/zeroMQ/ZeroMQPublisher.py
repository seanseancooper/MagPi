from datetime import datetime

import zmq
import json
import logging

net_logger = logging.getLogger('net_logger')

class ZeroMQPublisher:
    """
    Publish wifi retriever data to subscriber.
    ZeroMQPublisher: Produce a 'message' composed of:
            metadata: a mapping of iteration and scanned data.
            data: None
    """
    def __init__(self):
        context = zmq.Context()

        self.socket = context.socket(zmq.PUB)       # make configurable
        self.socket.bind("tcp://127.0.0.1:5555")    # make configurable host & port

    def send_data(self, data):
        message = json.dumps(data).encode('utf-8')
        self.socket.send(message)

    def test(self):
        scanned = ""

        data = {
            'id'     : 0,
            'sent'   : str(datetime.now()),
            "scanned": scanned,
        }

        return data


if __name__ == "__main__":
    producer = ZeroMQPublisher()
    data = producer.test()

    while True:
        producer.send_data(data)
