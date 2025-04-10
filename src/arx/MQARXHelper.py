from src.config import readConfig


class MQARXHelper:
    """ convert, transform and pass audio data """
    def __init__(self):
        super().__init__()

        self.config = {}

    def configure(self, config_file):
        readConfig(config_file, self.config)

    def run(self):
        pass



