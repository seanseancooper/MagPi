import threading

import zmq
import logging

net_logger = logging.getLogger('net_logger')

class ZeroMQProxy(threading.Thread):
    """
    XSUBZeroMQProxy to decouple wifi retriever data.
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
