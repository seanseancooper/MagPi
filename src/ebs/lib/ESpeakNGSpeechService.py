import shutil
import subprocess

from src.ebs.lib.SpeechService import SpeechService


class ESpeakNGSpeechService(SpeechService):
    """ ESpeakNG specific implementation of speech using local espeak command.
     This is targeted to GNU platforms and is a secondary focus due to
     anticipated disconnected environment """
    def __init__(self):
        super().__init__()
        self.config = {}

    def configure(self):
        super(ESpeakNGSpeechService, self).config()

    def process_message(self):
        if self.read_msg:
            command = ['espeak', self.read_msg]

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




