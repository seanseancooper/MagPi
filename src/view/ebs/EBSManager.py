import threading
import logging
import time

from src.config import readConfig
from src.view.ebs.lib.MacOSSpeechService import MacOSSpeechService

logger_root = logging.getLogger('root')
ebs_logger = logging.getLogger('ebs_logger')


class EBSManager(threading.Thread):

    def __init__(self):
        super().__init__()
        self.config = {}
        self.speechservice = None
        self.bugger = None

    def configure(self, config_file):
        readConfig(config_file, self.config)

    def enunciate(self, msg):
        if not self.speechservice:
            self.ebs_start()
            pass
        self.speechservice.enunciator.broadcast(msg)
        return

    def ebs_start(self):
        # Enunciator: Provide auditory feedback on events. This will pass
        # a message to a queue which is read by an interface for a
        # SpeechService, which will render it.

        self.speechservice = MacOSSpeechService()  # TODO: Make configurable, see CAMManager
        self.speechservice.configure()
        self.speechservice.init()

        s_thread = threading.Thread(target=self.speechservice.run, daemon=True, name='SpeechService')
        e_thread = threading.Thread(target=self.speechservice.enunciator.run, daemon=True, name='Enunciator')
        s_thread.start()
        e_thread.start()

        ebs_logger.debug(f's_thread: {s_thread.__str__()}')
        ebs_logger.debug(f'e_thread: {e_thread.__str__()}')

        time.sleep(.1)                  # needs time to startup!

    def run(self):
        self.ebs_start()


if __name__ == '__main__':
    e = EBSManager()
    e.run()
