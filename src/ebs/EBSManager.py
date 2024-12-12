import threading
import logging

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
        self.speechService.enunciator.broadcast(msg)
        return

    def stop(self):
        pass

    def ebs_start(self):
        # 2 components running in somewhat opposing threads:

        # Enunciator: Provide auditory feedback on events. This will pass
        # a message to a queue which is read by an interface for a
        # SpeechService, which will render it.

        self.speechService = MacOSSpeechService()  # TODO: Make configurable
        self.speechService.configure()
        self.speechService.init()
        thread = threading.Thread(target=self.speechService.run, daemon=True)
        thread.start()


        # Bugger: Uses ARX component to listen for and operationalize
        # spoken word commands from a library (project-keyword-spotter).
        # The library will use the Coral adapter to run inference on MFCC
        # slices in real time.
        #

    def run(self):
        self.ebs_start()


