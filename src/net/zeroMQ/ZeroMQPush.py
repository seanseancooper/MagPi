import threading
from datetime import datetime

import zmq
import json
import logging

net_logger = logging.getLogger('net_logger')

class ZeroMQPush(threading.Thread):
    """
    Publish wifi retriever data to subscriber.
    ZeroMQPublisher: Produce a 'message' composed of:
        {
            'id'     : 0,
            'sent'   : str(datetime.now()),
            "scanned": scanned,
        }
            metadata: a mapping of iteration, time 'sent' and scanned data.
    """
    def __init__(self):
        super().__init__()
        context = zmq.Context().instance()

        # PUSH/PULL
        self.socket = context.socket(zmq.PUSH)       # make configurable
        self.socket.connect("tcp://127.0.0.1:5555")    # make configurable host & port

    def send_data(self, data):
        self.socket.send(json.dumps(data).encode('utf-8'))

    def test(self):
        scanned = ""

        data = {
            'id'     : 0,
            'sent'   : str(datetime.now()),
            "scanned": scanned,
        }

        return data


if __name__ == "__main__":
    push = ZeroMQPush()
    data = push.test()

    while True:
        push.send_data(data)
