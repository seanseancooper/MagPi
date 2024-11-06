import os
import subprocess
import threading

import logging
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
            map_logger.info(f"[{__name__}]: running {command[3].upper()} \"{command[2]}\"")
        except Exception as e:
            pass  # missing element, etc. don't care

        try:
            # DBUG: This isn't safe. I need to be checking the PATH.
            #  Warning: For maximum reliability, use a fully qualified path for the executable.
            #
            #  To search for an unqualified name on PATH, use shutil.which().
            #
            #  On all platforms, passing sys.executable is the recommended way to launch the current Python
            #  interpreter again, and use the -m command-line format to launch an installed module.
            #
            #  Resolving the path of executable (or the first item of args) is platform dependent.
            #  For POSIX, see os.execvpe(), and note that when resolving or searching for the executable
            #  path, cwd overrides the current working directory and env can override the PATH environment
            #  variable.
            #
            #  For Windows, see the documentation of the lpApplicationName and lp
            #  CommandLine parameters of WinAPI CreateProcess, and note that when resolving
            #  or searching for the executable path with shell=False, cwd does not override
            #  the current working directory and env cannot override the PATH environment
            #  variable. Using a full path avoids all of these variations.

            # DBUG: the issue is that the fake systemctl isn't on the PATH and is being mis-executed
            # print(os.environ['PATH'])
            # os.execvpe(command[0], command[1:], os.environ)

            ps = subprocess.Popen(command)
            map_logger.debug(f"[{__name__}]: PID --> {ps.pid}")
            return ps.pid
        except OSError as e:
            map_logger.error(f"[{__name__}]:couldn't create a process for \'{command}\': {e}")
        return 0

    def node_stop(self):
        command = self.config['NODE_STOP_COMMAND'].append(str(self.pid))

        if self.runOSCommand(command) > 0:
            map_logger.info(f"[{__name__}]: OK")
        else:
            map_logger.error(f"[{__name__}]: FAIL! Verify NODE_STOP_COMMAND: {self.config['NODE_STOP_COMMAND']} "
                             f" is correctly formed.")

    def node_build(self):
        command = self.config['NODE_BUILD_COMMAND'].append(str(self.pid))

        if self.runOSCommand(command) > 0:
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
        else:
            map_logger.error(f"[{__name__}]: FAIL! Verify NODE_START_COMMAND: {self.config['NODE_START_COMMAND']} "
                             f"is correctly formed.")


if __name__ == '__main__':

    node = NodeRunner()
    node.configure(os.path.join(CONFIG_PATH, 'gps.json'))
    node.run()

