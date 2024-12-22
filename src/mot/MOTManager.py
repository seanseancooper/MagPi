import threading
import logging
import time

from src.config import readConfig
from src.lib.utils import runOSCommand


logger_root = logging.getLogger('root')
mot_logger = logging.getLogger('mot_logger')


class MOTManager(threading.Thread):

    def __init__(self):
        super().__init__()
        self.config = {}

    def __str__(self):
        return f"MOTManager: {str(self.config)}"

    def configure(self, config_file):
        readConfig(config_file, self.config)

    def stop(self):
        if runOSCommand(self.config['STOP_COMMAND']) > 0:
            return 0
        else:
            return None

    def start(self):
        if runOSCommand(self.config['START_COMMAND']) > 0:
            return "OK"
        else:
            return "FAIL!"

    def motion_controlpanel(self):
        return self.config['MOT']['MOTION_CPANEL_URL']

    def run(self):
        # self.start()
        while True:
            try:
                time.sleep(self.config['TIMEOUT'])
            except KeyboardInterrupt:
                exit(0)
