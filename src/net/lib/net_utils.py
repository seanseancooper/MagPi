
# class WifiWorkerParser:
#
#     def __init__(self, data):
#         self.data = data
#         self.worker_data = {}
#         self.signal_data = {}
#         self.signal_test = {}
#         self._parse()
#
#     def _parse(self):
#         self.worker_data = self.data
#
#         # transform created, updated representations to have a timezone
#         # worker_created_time = datetime.strptime(worker_data['created'], self.config['DATETIME_FORMAT'])
#         # worker_data['created'] = worker_created_time.astimezone().isoformat()
#         #
#         # worker_updated_time = datetime.strptime(worker_data['updated'], self.config['DATETIME_FORMAT'])
#         # worker_data['updated'] = worker_updated_time.astimezone().isoformat()
#
#         self.signal_data = [_ for _ in self.worker_data['signal_cache']]
#         # self.signal_test = self.worker_data['results']
#
#         # self.worker_data.pop('signal_cache')    # remove the signal cache
#         # self.worker_data.pop('results')         # remove the tests
#
#     def get_worker_data(self):
#         return self.worker_data
#
#     def get_signal_data(self):
#         return self.signal_data
#
#     def get_test_data(self):
#         return self.signal_test

class WifiWorkerParser:

    def __init__(self, data):
        self.data = data

    def get_worker_data(self):
        return {
            "id"        : self.data["id"],
            "SSID"      : self.data["SSID"],
            "BSSID"     : self.data["BSSID"],
            "created"   : self.data["created"],
            "updated"   : self.data["updated"],
            "elapsed"   : self.data["elapsed"],
            "Vendor"    : self.data["Vendor"],
            "Channel"   : self.data["Channel"],
            "Frequency" : self.data["Frequency"],
            "Signal"    : self.data["Signal"],
            "Quality"   : self.data["Quality"],
            "Encryption": self.data["Encryption"],
            "is_mute"   : self.data["is_mute"],
            "tracked"   : self.data["tracked"],
            "tests"     : self.data.get("tests", [])
        }

    def get_signal_data(self):
        return [
            {
                "created"  : signal["created"],
                "id"       : signal["id"],
                "worker_id": signal["worker_id"],
                "lat"      : signal["lat"],
                "lon"      : signal["lon"],
                "sgnl"     : signal["sgnl"]
            }
            for signal in self.data.get("signal_cache", [0])
        ]


