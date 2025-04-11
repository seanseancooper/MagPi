from src.config import readConfig
from src.net.zeromQ.ZeroMQAsyncProducer import ZeroMQAsyncProducer
from src.net.zeromQ.ZeroMQAsyncConsumer import ZeroMQAsyncConsumer



class ZeroMQARXHelper:
    """ convert, transform and pass audio arrays and stream data around """
    def __init__(self):
        super().__init__()

        self.config = {}

    def configure(self, config_file):
        readConfig(config_file, self.config)

    def run(self):
        pass



