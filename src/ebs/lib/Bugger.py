import threading

from src.arx.ARXRecorder import ARXRecorder
from src.config import readConfig


class Bugger(threading.Thread):

    def __init__(self):
        super().__init__()
        self.config = {}
        self.arxRec = None

    # Bugger: Uses ARX component to listen for and operationalize
    # spoken word commands from a library (project-keyword-spotter).
    # The library will use the Coral adapter to run inference on MFCC
    # slices in real time.

    def configure(self):
        readConfig('ebs.json', self.config)

    def init(self):
        self.arxRec = ARXRecorder()
        self.arxRec.configure('arx.json')

    def run(self):
        self.arxRec.run()
