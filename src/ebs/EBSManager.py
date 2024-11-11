import threading
import logging

from src.config import readConfig
from src.lib.utils import runOSCommand

logger_root = logging.getLogger('root')
ebs_logger = logging.getLogger('ebs_logger')


class EBSManager(threading.Thread):

    def __init__(self):
        super().__init__()
        self.config = {}

    def __str__(self):
        return {"EBSManager": str(self.config)}

    def configure(self, config_file):

        if not config_file:
            exit(1)

        readConfig(config_file, self.config)

    def ebs_stop(self):
        if runOSCommand(self.config['EBS']['STOP_COMMAND']) > 0:
            return 0
        else:
            return None

    def ebs_start(self):
        if runOSCommand(self.config['START_COMMAND']) > 0:
            return "OK"
        else:
            return "FAIL!"

    def run(self):
        self.ebs_start()
        # while True:
        #     try:
        #         time.sleep(1)
        #     except KeyboardInterrupt:
        #         exit(0)
