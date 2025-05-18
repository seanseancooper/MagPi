import os
import shutil
import signal
import subprocess
import threading
import logging
import time

import psutil

from src.config import readConfig

gps_logger = logging.getLogger('gps_logger')
DEADCODES = (psutil.STATUS_DEAD, psutil.STATUS_ZOMBIE,)

def runOSCommand(command: list):
    try:
        command[0] = shutil.which(command[0])
        ps = subprocess.Popen(command)
        gps_logger.debug(f"[{__name__}]: PID --> {ps.pid}")
        return ps.pid
    except OSError as e:
        gps_logger.fatal(f"[{__name__}]:couldn't create a process for \'{command}\': {e}")
    return 0


def kills_pids_and_kids(pid):
    """
    Removes a pid and all children representing a display process from
    the _processes dict. As deadly as it sounds; it's static so it can
    be called externally to the class instance.

    :param pid: process id to be found and removed
    :exception NoSuchProcess
    :return True if successful
    """
    try:

        ps = psutil.Process(pid)
        [_.send_signal(signal.SIGTERM) for _ in ps.children(recursive=True)]
        ps.terminate()
        gps_logger.info(f"[{__name__}]: pid {pid} killed.")
        return True

    except psutil.NoSuchProcess:
        gps_logger.warning(f"[{__name__}]: Failed to find pid:{pid} to kill.")



class NodeRunner(threading.Thread):

    def __init__(self):
        super().__init__()
        self.pid = 0
        self.config = {}

    def configure(self, config_file):

        if not config_file:
            exit(1)

        readConfig(config_file, self.config)


    def build(self):
        if runOSCommand(self.config['NODE_BUILD_COMMAND']) > 0:
            time.sleep(5)
            gps_logger.info(f"[{__name__}]: OK")
        else:
            gps_logger.error(f"[{__name__}]: FAIL! Verify NODE_BUILD_COMMAND: {self.config['NODE_BUILD_COMMAND']} "
                             f" is correctly formed.")

    def run(self):
        home = os.getcwd()
        self.pid = runOSCommand(self.config['NODE_START_COMMAND'])
        if self.pid > 0:
            os.chdir(home)
            gps_logger.info(f"[{__name__}]: OK {self.pid}")

            return self.pid
        else:
            gps_logger.error(f"[{__name__}]: FAIL! Verify NODE_START_COMMAND: {self.config['NODE_START_COMMAND']} "
                             f"is correctly formed.")

    def stop(self):
        if self.pid > 0:
            return kills_pids_and_kids(self.pid)
            


if __name__ == '__main__':

    node = NodeRunner()
    node.configure('map.json')
    node.run()

