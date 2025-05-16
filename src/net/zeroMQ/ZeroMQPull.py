import threading
from datetime import datetime

import zmq
import json
import logging

net_logger = logging.getLogger('net_logger')

class ZeroMQPull(threading.Thread):
    """
    ZeroMQPull: bind to a socket and PULL data from PUSH.
    The PUSH/PULL pattern is really a pipelining mechanism.
    PUSH/PULL doesn’t drop messages when there’s no recipient.
    PUSH blocks when there’s no Peer ready to receive a message
    """
    def __init__(self, I_ZMQ_HOST, I_ZMQ_PORT):
        super().__init__()
        self.host = I_ZMQ_HOST
        self.port = I_ZMQ_PORT
        context = zmq.Context().instance()

        self.socket = context.socket(zmq.PULL)
        self.socket.bind(f'tcp://{self.host}:{self.port}')            # make configurable host & port

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
    pull = ZeroMQPull(host, port)
    while True:
        # pull.receive_data()
        import asyncio
        asyncio.run(pull.receive_data())
