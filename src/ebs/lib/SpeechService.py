import queue
import threading
import time
import logging
from src.config import readConfig
from src.ebs.lib.Enunciator import Enunciator

ebs_logger = logging.getLogger('ebs_logger')


class SpeechService(threading.Thread):

    """ superclass for all types of speech providers.
     produces a SpeechService queue (that it owns
     owned) for messages too travverse """

    def __init__(self):
        super().__init__()
        self.config = {}
        self.enunciator = None
        self.rate = None
        self.voice = None
        self.message_queue = None
        self.read_msg = None

    def config(self):
        readConfig('ebs.json', self.config)
        self.rate = self.config['SPEECH_RATE']
        self.voice = self.config['SPEECH_VOICE']

    def init(self):
        # TODO: perhaps reevaluate how this is being started.
        self.enunciator = Enunciator('name', 1, 100)
        self.enunciator.speechservice = self
        self.enunciator.configure()
        self.enunciator.init()

    def make_fifo(self):
        self.message_queue = queue.Queue(maxsize=1)
        return self.message_queue

    def enqueue(self, m):
        self.message_queue.put(m, block=True, timeout=None)

    def dequeue(self):
        while not self.message_queue.empty():
            self.read_msg = self.message_queue.get()

    def process_message(self):
        """  overridden in implementation """
        pass

    def run(self):
        while True:
            self.dequeue()
            self.process_message()
            time.sleep(.1)


