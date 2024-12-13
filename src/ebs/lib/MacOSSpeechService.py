import shutil
import subprocess

from src.ebs.lib.SpeechService import SpeechService


class MacOSSpeechService(SpeechService):
    """ MacOS specific implementation of speech using 'say'. This takes
    messages from superclass 'SpeechService' and renders them. """
    def __init__(self):
        super().__init__()
        self.config = {}

    def configure(self):
        super(MacOSSpeechService, self).config()

    def process_message(self):
        # MacOS specific impl to render message
        if self.read_msg:
            command = ['say', '-r', str(self.rate), '-v', self.voice, self.read_msg]

            def runBlockingOSCommand(command: list):
                try:
                    command[0] = shutil.which(command[0])
                    ps = subprocess.Popen(command)
                    ps.wait()                               # mandatory: block until message completes
                    return ps.pid
                except OSError as e:
                    print(f"[{__name__}]:couldn't create a process for \'{command}\': {e}")
                return 0

            pid = runBlockingOSCommand(command)
            if pid > 0:
                self.read_msg = None

