import json
from datetime import datetime, timedelta, timezone
from src.net.elastic.ElasticClientProvider import ElasticClient as ElasticClient
from WifiWorkerParser import WifiWorkerParser
from src.config import readConfig


class WifiElasticMappingTransformer:

    def __init__(self):

        self.client = None
        self.worker_index_mapping = None
        self.signals_index_mapping = None
        self.tz = None
        self._seen = []
        self.config = {}

    def configure(self):

        readConfig('wifi.json', self.config)

        provider = ElasticClient()
        self.client = provider.get_client('net.json')

        self.worker_index_mapping = self.config['WORKER_INDEX_MAPPING']
        self.signals_index_mapping = self.config['SIGNALS_INDEX_MAPPING']
        self.tz = timezone(timedelta(hours=self.config['INDEX_TIMEDELTA']), name=self.config['INDEX_TZ'])

        if self.client:
            # Create workers index, ignore warning that it exists.
            self.client.indices.create(index='workers', body=self.worker_index_mapping, ignore=400)

    def update_wifi_worker(self, worker_data, signal_data):

        # transform 'updated' representation to have a timezone
        worker_updated_time = datetime.strptime(worker_data['updated'], self.config['DATETIME_FORMAT'])
        worker_data['updated'] = worker_updated_time.astimezone(self.tz).isoformat()

        updt_worker_doc = {
            "updated": worker_data['updated'],
            "elapsed": worker_data['elapsed'],

            "Channel"  : int(worker_data['Channel']),
            "Frequency": int(worker_data['Frequency']),
            "Signal"   : int(worker_data['Signal']),
            "Quality"  : int(worker_data['Quality']),

            "is_mute": worker_data['is_mute'],
            "signal_cache": [self.get_signalpoint(signal) for signal in signal_data]
        }

        worker_index = f"worker_{worker_data['id']}"
        self.client.update(index=worker_index, id=worker_data['id'], doc=updt_worker_doc, ignore=400)

    def process_workers(self, data):

        for item in data:
            parser = WifiWorkerParser(item)
            worker_data = parser.get_worker_data()
            signal_data = parser.get_signal_data()

            if worker_data['id'] in self._seen:
                self.update_wifi_worker(worker_data, signal_data)
            else:
                # Insert worker data
                worker_id = worker_data['id']
                worker_index = f"worker_{worker_id}"

                # transform created, updated representations to have a timezone
                worker_created_time = datetime.strptime(worker_data['created'], self.config['DATETIME_FORMAT'])
                worker_data['created'] = worker_created_time.astimezone(self.tz).isoformat()

                worker_updated_time = datetime.strptime(worker_data['updated'], self.config['DATETIME_FORMAT'])
                worker_data['updated'] = worker_updated_time.astimezone(self.tz).isoformat()

                worker_doc = {
                    **worker_data,
                    "Channel"  : int(worker_data['Channel']),
                    "Frequency": int(worker_data['Frequency']),
                    "Signal"   : int(worker_data['Signal']),
                    "Quality"  : int(worker_data['Quality']),
                    "signal_cache": [self.get_signalpoint(signal) for signal in signal_data]
                }

                # Index worker document
                self.client.index(index=worker_index, id=worker_id, document=worker_doc, ignore=400)

                # Create signal index for worker
                signals_index = f"{worker_data['id']}_signals"
                self.client.indices.create(index=signals_index, body=self.signals_index_mapping, ignore=400)

    def get_signalpoint(self, sgnl):

        # transforms created representations to have a timezone
        sgnl_created_time = datetime.strptime(sgnl["created"], "%Y-%m-%d %H:%M:%S")
        sgnl["created"] = sgnl_created_time.astimezone(self.tz).isoformat()

        return {
            "created"  : sgnl["created"],
            "id"       : sgnl["id"],
            "worker_id": sgnl["worker_id"],
            "location" : {"lat": float(sgnl["lat"]), "lon": float(sgnl["lon"])},
            "sgnl"     : int(sgnl["sgnl"])
        }

    def process_signals(self, data):

        for item in data:
            parser = WifiWorkerParser(item)
            worker_data = parser.get_worker_data()
            signal_data = parser.get_signal_data()

            # Create signal index if needed
            signals_index = f"{worker_data['id']}_signals"

            def _index(idx, sgnl):
                """ index, signalpoint """

                signal_doc = self.get_signalpoint(sgnl)
                self.client.index(index=idx, id=sgnl["id"], document=signal_doc)

            if worker_data['id'] in self._seen:
                _index(signals_index, signal_data[-1])
            else:
                [_index(signals_index, signal) for signal in signal_data if signal_data]
                self._seen.append(worker_data['id'])

    def push(self, data):
        """ method entrypoint for elastic indexing """
        try:
            self.process_workers(data)
            self.process_signals(data)
            print(f"Data pushed: {datetime.now().astimezone(self.tz).isoformat()}")
        except Exception as ex:
            print(f"Data push failed: {ex}")
            exit(1)

    def pull(self, mod='wifi'):
        # get current list of elastic worker_id indexes from elastic (less 201s)
        # get boolean signal id: is item in list?
        # run queries and get data.
        pass

if __name__ == '__main__':

    e = WifiElasticMappingTransformer()
    it = WifiWorkerParser
    e.configure()
    # push 'training data' into elastic.
    with open('/dev/wifi/training_data/scanlists_out.json', 'r') as f:
        data = json.load(f)
        e.client.push(data)