from src.ebs.lib.GenericSpeechService import SpeechService
from src.lib.utils import runOSCommand


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

    def process_message(self):
        # MacOS specific impl to render message
        if self.read_msg:
            command = ['say', '-r', '200', self.read_msg]
            pid = runOSCommand(command)
            self.read_msg = None
            print(f'command: {command} pid: {pid}')

    def shutdown(self):
        pass





