import threading


class SDRWorker(threading.Thread):


    def __init__(self):
        super().__init__()
        self.config = {}
