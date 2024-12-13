import threading


class Bugger(threading.Thread):

    def __init__(self):
        super().__init__()
        self.config = {}

    # Bugger: Uses ARX component to listen for and operationalize
    # spoken word commands from a library (project-keyword-spotter).
    # The library will use the Coral adapter to run inference on MFCC
    # slices in real time.
