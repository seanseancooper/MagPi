import threading

import zmq
import logging

net_logger = logging.getLogger('net_logger')

class ZeroMQProxy(threading.Thread):
    """
    ZeroMQProxy: Decouple PUSH from PULL; bind to an input socket and
    an output socket. PULL from the input socket and PUSH same out of
    the output socket. There will always be a socket to connect to,
    though data may be not be available or read.
    """
    def __init__(self, i_url, o_url):
        super().__init__()
        self.i_url = i_url
        self.o_url = o_url

    def run(self):
        i_url = self.i_url
        o_url = self.o_url

        ctx = zmq.Context.instance()
        in_s = ctx.socket(zmq.PULL)
        in_s.bind(i_url)
        out_s = ctx.socket(zmq.PUSH)
        out_s.bind(o_url)

        try:
            print("starting proxy")
            zmq.proxy(in_s, out_s)
            print("proxy started")

        except zmq.ContextTerminated:
            print("proxy terminated")
            in_s.close()
            out_s.close()

if __name__ == "__main__":
    i_url = ''
    o_url = ''
    proxy = ZeroMQProxy(i_url, o_url)
