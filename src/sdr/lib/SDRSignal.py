from datetime import datetime, timedelta


class SDRSignal:

    def __init__(self, data):
        self._data = data
        self.created = datetime.now()   # when signal was found
        self.updated = datetime.now()   # when signal was last reported
        self.elapsed = timedelta()      # length of signal



