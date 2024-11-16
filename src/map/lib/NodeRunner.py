import os
import shutil
import subprocess
import threading

import logging
import time

from src.config import CONFIG_PATH, readConfig

map_logger = logging.getLogger('gps_logger')


class NodeRunner(threading.Thread):

    def __init__(self):
        super().__init__()
        self.pid = 0
        self.config = {}

    def configure(self, config_file):

        if not config_file:
            exit(1)

        readConfig(config_file, self.config)

    def runOSCommand(self, command: list):
        try:
            command[0] = shutil.which(command[0])
            ps = subprocess.Popen(command)
            map_logger.debug(f"[{__name__}]: PID --> {ps.pid}")
            return ps.pid
        except OSError as e:
            map_logger.error(f"[{__name__}]:couldn't create a process for \'{command}\': {e}")
        return 0

    def build(self):
        if self.runOSCommand(self.config['NODE_BUILD_COMMAND']) > 0:
            time.sleep(5)
            map_logger.info(f"[{__name__}]: OK")
        else:
            map_logger.error(f"[{__name__}]: FAIL! Verify NODE_BUILD_COMMAND: {self.config['NODE_BUILD_COMMAND']} "
                             f" is correctly formed.")

    def run(self):
        home = os.getcwd()
        self.pid = self.runOSCommand(self.config['NODE_START_COMMAND'])
        if self.pid > 0:
            os.chdir(home)
            map_logger.info(f"[{__name__}]: OK {self.pid}")

            return self.pid
        else:
            map_logger.error(f"[{__name__}]: FAIL! Verify NODE_START_COMMAND: {self.config['NODE_START_COMMAND']} "
                             f"is correctly formed.")


if __name__ == '__main__':

    node = NodeRunner()
    node.configure(os.path.join(CONFIG_PATH, 'gps.json'))
    node.run()

