from datetime import datetime, timedelta


class Signal:

    def __init__(self, sr, data):
        self._data = data
        self.created = datetime.now()   # when signal was found
        self.updated = datetime.now()   # when signal was last reported
        self.elapsed = timedelta()      # length of signal
        self.sr = sr                    # sampling rate of signal
        self.data = None                # [ndarray: container] data of T
        self.attributes = {             # map of signal attributes (add as needed)
            "source": None,
            "type": None,
            "mono": None,
            "tag": None
        }


