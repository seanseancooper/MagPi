import threading
import logging
import time

from src.config import readConfig
from src.ebs.lib.MacOSSpeechService import MacOSSpeechService

logger_root = logging.getLogger('root')
ebs_logger = logging.getLogger('ebs_logger')


class EBSManager(threading.Thread):

    def __init__(self):
        super().__init__()
        self.config = {}
        self.speechService = None

    def configure(self, config_file):
        readConfig(config_file, self.config)

    def enunciate(self, msg):
        if not self.speechService:
            self.ebs_start()
            pass
        self.speechService.enunciator.broadcast(msg)
        return

    def ebs_start(self):
        # 2 components running in somewhat opposing threads:

        # Enunciator: Provide auditory feedback on events. This will pass
        # a message to a queue which is read by an interface for a
        # SpeechService, which will render it.

        self.speechService = MacOSSpeechService()  # TODO: Make configurable
        self.speechService.configure()
        self.speechService.init()

        s_thread = threading.Thread(target=self.speechService.run, daemon=True, name='SpeechService')
        e_thread = threading.Thread(target=self.speechService.enunciator.run, daemon=True, name='Enunciator')
        s_thread.start()
        e_thread.start()
        ebs_logger.debug(f's_thread: {s_thread.__str__()}')
        ebs_logger.debug(f'e_thread: {e_thread.__str__()}')

        time.sleep(.1)                  # needs time to startup!
        self.enunciate("EBS")           # best place for this w/o dual startup

        # Bugger: Uses ARX component to listen for and operationalize
        # spoken word commands from a library (project-keyword-spotter).
        # The library will use the Coral adapter to run inference on MFCC
        # slices in real time.

    def run(self):
        self.ebs_start()
