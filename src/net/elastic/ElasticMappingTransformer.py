import json
from datetime import datetime, timedelta, timezone
from src.net.elastic.ElasticClientProvider import ElasticClient as ElasticClient
from src.config import readConfig


class ElasticMappingTransformer:

    def __init__(self, mapTxfmr):

        self.client = None
        self.worker_index_mapping = None
        self.signals_index_mapping = None
        self.signals_data = None
        self.tz = None
        self._seen = []
        self.config = {}
        self.mapTxfmr = mapTxfmr

    def configure(self, config_file):

        readConfig(config_file, self.config)

        provider = ElasticClient()
        self.client = provider.get_client('net.json')

        self.worker_index_mapping = self.config['WORKER_INDEX_MAPPING']
        self.signals_index_mapping = self.config['SIGNALS_INDEX_MAPPING']
        self.tz = timezone(timedelta(hours=self.config['INDEX_TIMEDELTA']), name=self.config['INDEX_TZ'])

        if self.client:
            # Create workers index, ignore warning that it exists.
            self.client.indices.create(index='workers', body=self.worker_index_mapping, ignore=400)

    def update_worker(self, worker_data, signal_data):

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

    def process_worker(self, item):

        parser = self.mapTxfmr(item)
        worker_data = parser.get_worker_data()

        # this entire choice should be higher, earlier and remove signal_data and deps from this method
        self.signals_data = parser.get_signal_data()  # why is signal data here in a worker method.

        if worker_data['id'] in self._seen:
            self.update_worker(worker_data, self.signals_data)
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
                "signal_cache": [self.get_signalpoint(signal) for signal in self.signals_data]
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

    def process_signals(self, item):

        parser = self.mapTxfmr(item)
        worker_data = parser.get_worker_data()
        self.signals_data = parser.get_signal_data()

        # Create signal index if needed
        signals_index = f"{worker_data['id']}_signals"

        def _index(idx, sgnl):
            """ index, signalpoint """

            signal_doc = self.get_signalpoint(sgnl)
            self.client.index(index=idx, id=sgnl["id"], document=signal_doc)

        if worker_data['id'] in self._seen:
            _index(signals_index, self.signals_data[-1])
        else:
            [_index(signals_index, signal) for signal in self.signals_data if self.signals_data]
            self._seen.append(worker_data['id'])

    def push(self, data):
        """ method entrypoint for elastic indexing """
        try:

            [self.process_signals(item) for item in data]

            parsers = [self.mapTxfmr(item) for item in data]
            parsed_workers = [parsed.get_worker_data() for parsed in parsers]

            def worker_sorter(parsed_worker):
                if parsed_worker.get('id') in self._seen:
                    [self.process_worker(item) for item in data]  # uses self.signal_data
                else:
                    [self.process_worker(item) for item in data]
                    self._seen.append(parsed_worker['id'])

            [worker_sorter(worker) for worker in parsed_workers]

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
    from src.wifi.lib.WifiWorkerParser import WifiWorkerParser
    mapTxfmr = WifiWorkerParser

    e = ElasticMappingTransformer(mapTxfmr)  # <-- pass it a transformer ()
    e.configure('wifi.json')
    # push 'training data' into elastic.
    with open('/dev/wifi/training_data/scanlists_out.json', 'r') as f:
        data = json.load(f)
        e.client.push(data)