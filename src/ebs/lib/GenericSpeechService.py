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
        self.message_queue = None
        # DO NOT put a field for a specific impl; we want to be able to render to multiple impls simultaneously.
        self.read_msg = None

    def config(self):
        # generic config
        readConfig('ebs.json', self.config)

    def init(self):
        # Create a new Enunciator instance.
        self.enunciator = Enunciator('name', 1, 100)
        self.enunciator.speech = self
        self.enunciator.configure()
        self.enunciator.init()
        threading.Thread(target=self.enunciator.run).start()

    def make_fifo(self):
        self.message_queue = queue.Queue(maxsize=1)
        return self.message_queue

    def write_queue(self, m):
        while self.message_queue.empty():
            self.message_queue.put(m)

    def read_queue(self):
        # read whatever has queued messsages.
        while not self.message_queue.empty():
            self.read_msg = self.message_queue.get()

    def process_message(self):
        # implemented in a subclass
        pass

    def shutdown(self):
        # run my & specific shutdowns, nest.
        pass

    def run(self):
        while True:
            self.read_queue()
            self.process_message()   # runs a thread; dispose when done


