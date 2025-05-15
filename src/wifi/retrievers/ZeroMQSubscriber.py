import threading
from datetime import datetime

import zmq
import json
import logging
net_logger = logging.getLogger('net_logger')

class ZeroMQSubscriber(threading.Thread):
    """
    Consume wifi retriever data.
    ZeroMQ Subscriber: consume a 'message' composed of:
            metadata: a mapping of iteration and scanned data.
            data: None
    """
    def __init__(self):
        super().__init__()
        context = zmq.Context().instance()

        # PUB/SUB *
        # pub/sub pattern is used for wide message distribution according to topics.
        # PUB socket sends the same message to all subscribers
        # if the publishing node sends data through ZMQ.PUB but the subscriber is disconnected, the data will be dropped.
        self.socket = context.socket(zmq.SUB)                       # make configurable
        self.socket.connect("tcp://127.0.0.1:5555")                 # make configurable host & port
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
    consumer = ZeroMQSubscriber()
    while True:
        # consumer.receive_data()
        import asyncio
        asyncio.run(consumer.receive_data())
