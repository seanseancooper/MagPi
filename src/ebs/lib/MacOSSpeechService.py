import shutil
import subprocess

from src.ebs.lib.GenericSpeechService import SpeechService


class MacOSSpeechService(SpeechService):
    """ MacOS specific implementation of speech using local 'say' command.
     Takes messages from superclass SpeechService and renders them. This is
     a messaging consumer, subscriber.
     I need this right now."""
    def __init__(self):
        super().__init__()
        self.config = {}

    def configure(self):
        super(MacOSSpeechService, self).config()
        # MacOS specific config here
        # say
        # [-v voice] [-r rate]
        # [-o outfile [audio format options] | -n name:port | -a device]
        # [-f file | string ...]

    def process_message(self):
        # MacOS specific impl to render message
        if self.read_msg:
            command = ['say', '-r', str(self.rate), '-v', self.voice, self.read_msg]

            def runOSCommand(command: list):
                try:
                    command[0] = shutil.which(command[0])
                    ps = subprocess.Popen(command)
                    ps.wait()
                    return ps.pid
                except OSError as e:
                    print(f"[{__name__}]:couldn't create a process for \'{command}\': {e}")
                return 0

            pid = runOSCommand(command)
            if pid > 0:
                self.read_msg = None
                # self.message_queue.join()

    def shutdown(self):
        pass





