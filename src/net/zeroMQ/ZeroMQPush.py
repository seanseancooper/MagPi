import threading
from datetime import datetime

import zmq
import json
import logging

net_logger = logging.getLogger('net_logger')

class ZeroMQPush(threading.Thread):
    """
    ZeroMQPush: connect to a socket and PUSH data to PULL.
    The PUSH/PULL pattern is really a pipelining mechanism.
    PUSH/PULL doesn’t drop messages when there’s no recipient.
    PUSH blocks when there’s no Peer ready to receive a message
    """
    def __init__(self):
        super().__init__()
        context = zmq.Context().instance()

        # PUSH/PULL
        self.socket = context.socket(zmq.PUSH)
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
