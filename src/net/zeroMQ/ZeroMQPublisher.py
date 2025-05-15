import threading
from datetime import datetime

import zmq
import json
import logging

net_logger = logging.getLogger('net_logger')

class ZeroMQPublisher(threading.Thread):
    """
    ZeroMQPublisher: bind to a socket and Publish a 'message' to a Subscriber.
    The PUB/SUB pattern is used for wide message distribution according to topics.
    A PUB socket sends the same message to all subscriber and drops messages when there’s no recipient.
    """
    def __init__(self):
        super().__init__()
        context = zmq.Context().instance()

        self.socket = context.socket(zmq.PUB)
        self.socket.bind("tcp://127.0.0.1:5555")    # make configurable host & port

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
    publisher = ZeroMQPublisher()
    data = publisher.test()

    while True:
        publisher.send_data(data)
