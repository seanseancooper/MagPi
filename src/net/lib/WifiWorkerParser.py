


class WifiWorkerParser:

    def __init__(self, data):
        self.data = data
        self.worker_data = {}
        self.signal_data = {}
        self.signal_test = {}
        self._parse()

    def _parse(self):
        self.worker_data = self.data
        self.signal_data = self.worker_data['signal_cache']
        self.signal_test = self.worker_data['results']

        self.worker_data.pop('signal_cache')    # remove the signal cache
        self.worker_data.pop('results')         # remove the tests

    def get_worker_data(self):
        return self.worker_data

    def get_signal_data(self):
        return self.signal_data

    def get_test_data(self):
        return self.signal_test
