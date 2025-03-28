import os
import json
from datetime import datetime, timedelta, timezone
from elasticsearch import Elasticsearch
from src.net.lib.net_utils import WifiWorkerParser as WifiWorkerParser
from src.config import readConfig


class ElasticSearchIntegration:

    def __init__(self):

        self.client = None
        # self.index_requests = []
        # self.signals_requests = []
        self.worker_index_mapping = None
        self.signals_index_mapping = None
        self._seen = []
        self.config = {}

    def configure(self):
        readConfig('net.json', self.config)
        try:
            self.client = Elasticsearch(
                    self.config['ELASTIC_HOST'],
                    ca_certs=self.config['ELASTIC_CERT'],
                    basic_auth=(self.config['ELASTIC_USERNAME'], self.config['ELASTIC_PASSWORD']),
            )
        except ConnectionRefusedError:
            pass

        self.worker_index_mapping = self.config['WORKER_INDEX_MAPPING']
        self.signals_index_mapping = self.config['SIGNALS_INDEX_MAPPING']

        if self.client:
            print(f"Connected to Elasticsearch: {self.client.info()}")
            # Create workers index, ignore warning that it exists.
            self.client.indices.create(index='workers', body=self.worker_index_mapping, ignore=400)
        else:
            print(f"Failed to connect Elasticsearch. It is online?")
            exit(0)

    def update_worker(self, worker_data, signal_data):

        worker_index = f"worker_{worker_data['id']}"

        # transform updated representation to have a timezone
        worker_updated_time = datetime.strptime(worker_data['updated'], self.config['DATETIME_FORMAT'])
        worker_data['updated'] = worker_updated_time.astimezone().isoformat()

        worker_doc = {
            # only updates:
            "updated": worker_data['updated'],
            # "elapsed": worker_data['elapsed'],
            "is_mute": worker_data['is_mute'],
            "tracked": worker_data['tracked'],
            # "signal_cache": self.get_doc(signal_data[-1])
            "signal_cache": [self.get_doc(signal) for signal in signal_data]
        }

        self.client.update(index=worker_index, id=worker_data['id'], doc=worker_doc, ignore=400)

    def process_workers(self, data):

        for item in data:
            parser = WifiWorkerParser(item)
            worker_data = parser.get_worker_data()
            signal_data = parser.get_signal_data()

            if worker_data['id'] in self._seen:
                print(f"updating: {worker_data['SSID']} [{worker_data['id']}]")
                self.update_worker(worker_data, signal_data)
            else:
                # Insert worker data
                worker_id = worker_data['id']
                worker_index = f"worker_{worker_id}"
                print(f"indexing: {worker_data['SSID']} [{worker_data['id']}]")

                # transform created, updated representations to have a timezone
                worker_created_time = datetime.strptime(worker_data['created'], self.config['DATETIME_FORMAT'])
                worker_data['created'] = worker_created_time.astimezone().isoformat()

                worker_updated_time = datetime.strptime(worker_data['updated'], self.config['DATETIME_FORMAT'])
                worker_data['updated'] = worker_updated_time.astimezone().isoformat()

                worker_doc = {
                    **worker_data,
                    "signal_cache": [self.get_doc(signal) for signal in signal_data]
                    # "signal_cache": [signal for signal in signal_data]
                }

                # not this?
                # self.index_requests.append(f"PUT /{worker_index} {self.worker_index_mapping}")

                # Index worker document
                self.client.index(index=worker_index, id=worker_id, document=worker_doc, ignore=400)

                # Create signal index
                signals_index = f"{worker_data['id']}_signals"
                self.client.indices.create(index=signals_index, body=self.signals_index_mapping, ignore=400)

    @staticmethod
    def get_doc(sgnl):

        # transform created representations to have a timezone
        sgnl_created_time = datetime.strptime(sgnl["created"], "%Y-%m-%d %H:%M:%S")

        # not in here, make configurable/automatic.
        TimeDelta = timedelta(hours=6)
        TZObject = timezone(TimeDelta, name="MST")

        sgnl["created"] = sgnl_created_time.astimezone(TZObject).isoformat()

        return {
            "created"  : sgnl["created"],
            "id"       : sgnl["id"],
            "worker_id": sgnl["worker_id"],
            "location" : {"lat": sgnl["lat"], "lon": sgnl["lon"]},
            "sgnl"     : sgnl["sgnl"]
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

                signal_doc = self.get_doc(sgnl)
                self.client.index(index=idx, id=sgnl["id"], document=signal_doc)
                # self.signals_requests.append(f"POST /{idx}/_doc/{sgnl['id']} {signal_doc}")

            if worker_data['id'] in self._seen:
                _index(signals_index, signal_data[-1])
                print(f"updating signals for: {worker_data['SSID']} [{worker_data['id']}]")
            else:
                for signal in signal_data:
                    _index(signals_index, signal)
                self._seen.append(worker_data['id'])
                print(f"ingesting signals for: {worker_data['SSID']} [{worker_data['id']}]")

    def push(self, data):
        try:
            self.process_workers(data)
            self.process_signals(data)
            print(f"Data pushed successfully.")
        except Exception as e:
            print(f"Data push failed: {e}")

        # Save index requests for debugging
        # print(f"Export located @ {self.config['OUTFILE_PATH']}")
        # with open(os.path.abspath(self.config['OUTFILE_PATH']) + "/" + self.config['OUT_FILE'], 'w') as f:
        #     f.write("\n".join(self.index_requests))

        # with open('/Users/scooper/PycharmProjects/MagPi/src/net/signals_requests.json', 'w') as f:
        #     f.write("\n".join(self.signals_requests))

    def pull(self, mod='wifi'):
        # get current list of elastic worker_id indexes from elastic (less 201s)
        # get boolean signal id: is item in list?
        # run queries and get data.
        pass


if __name__ == '__main__':

    e = ElasticSearchIntegration()
    e.configure()

    with open('/Users/scooper/PycharmProjects/MagPi/dev/wifi/training_data/scanlists_out.json', 'r') as f:
        data = json.load(f)
        e.push(data)