import queue
import threading

from src.config import readConfig
from src.ebs.Enunciator import Enunciator


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
        # generic config
        readConfig('ebs.json', self.config)
        self.rate = self.config['SPEECH_RATE']
        self.voice = self.config['SPEECH_VOICE']

    def init(self):
        self.enunciator = Enunciator('name', 1, 100)
        self.enunciator.configure()
        self.enunciator.speech = self
        self.enunciator.init()
        threading.Thread(target=self.enunciator.run).start()

    def make_fifo(self):
        self.message_queue = queue.Queue(maxsize=1)
        return self.message_queue

    def enqueue(self, m):
        self.message_queue.put(m, block=True, timeout=None)

    def dequeue(self, n):
        while not self.message_queue.empty():           # this needs to block until message completes
            self.read_msg = self.message_queue.get()

    def process_message(self):
        pass

    def shutdown(self):
        pass

    def run(self):
        while True:
            self.dequeue(1)
            self.process_message()


