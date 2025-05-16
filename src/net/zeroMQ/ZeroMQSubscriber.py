import threading
from datetime import datetime

import zmq
import json
import logging

net_logger = logging.getLogger('net_logger')

class ZeroMQSubscriber(threading.Thread):
    """
    ZeroMQSubscriber: connect to a socket and read a 'message' from a Publisher.
    The PUB/SUB pattern is used for wide message distribution according to topics.
    SUB socket receives messages according to topic zmq.SUBSCRIBE
    """
    def __init__(self, I_ZMQ_HOST, I_ZMQ_PORT):
        super().__init__()
        self.host = I_ZMQ_HOST
        self.port = I_ZMQ_PORT
        context = zmq.Context().instance()

        self.socket = context.socket(zmq.SUB)
        self.socket.connect(f'tcp://{self.host}:{self.port}')       # make configurable host & port
        self.socket.setsockopt_string(zmq.SUBSCRIBE, '')            # make configurable

        self.message = None     # entire message
        self.data = None        # data as utf-8 decoded bytes.

    async def receive_data(self):

        self.message = self.socket.recv()
        self.data = json.loads(self.message.decode('utf-8'))

        self.data['time_diff'] = (datetime.now() - datetime.strptime(self.data['sent'], "%Y-%m-%d %H:%M:%S.%f")).total_seconds()

        # do something with data & text_attributes
        # print(f'time diff:{self.data["time_diff"]} iteration:{self.data["id"]}', end='\t')
        # net_logger.info(f'Received metadata: {self.data}')

    def get_message(self):
        return self.message

    def get_data(self):
        return self.data

if __name__ == "__main__":
    host = '127.0.0.1'
    port = 5555
    subscriber = ZeroMQSubscriber(host, port)
    while True:
        # consumer.receive_data()
        import asyncio
        asyncio.run(subscriber.receive_data())
