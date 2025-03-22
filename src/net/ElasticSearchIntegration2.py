from datetime import datetime

from elasticsearch import Elasticsearch
from src.config import CONFIG_PATH, readConfig

import os


class ElasticSearchIntegration:

    def __init__(self):
        self.client = None
        self.operations = []
        self.index_requests = []
        self.signals_requests = []
        self.worker_index_mapping = None
        self.signals_index_mapping = None
        self.config = {}

    def init(self):
        readConfig('net.json', self.config)
        try:
            self.client = Elasticsearch(
                    self.config['ELASTIC_HOST'],
                    ca_certs=self.config['ELASTIC_CERT'],
                    basic_auth=(self.config['ELASTIC_USERNAME'], self.config['ELASTIC_PASSWORD'])
            )
        except ConnectionRefusedError:
            pass

        if self.client:
            print(f"Connected to Elasticsearch: {self.client.info()}")
        else:
            exit(0)

        # Worker index mapping (Version 3)
        self.worker_index_mapping = {
            "mappings": {
                "properties": {
                    "id"          : {"type": "keyword"},
                    "SSID"        : {"type": "keyword"},
                    "BSSID"       : {"type": "keyword"},
                    "created"     : {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"},
                    "updated"     : {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"},
                    "elapsed"     : {"type": "date"},
                    "Vendor"      : {"type": "keyword"},
                    "Channel"     : {"type": "integer"},
                    "Frequency"   : {"type": "integer"},
                    "Signal"      : {"type": "integer"},
                    "Quality"     : {"type": "integer"},
                    "Encryption"  : {"type": "boolean"},
                    "is_mute"     : {"type": "boolean"},
                    "tracked"     : {"type": "boolean"},
                    # DO NOT INDEX SIGNAL CACHE HERE. UPDATE!
                    "signal_cache": {
                        "type"      : "nested",
                        "properties": {
                            "created"  : {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"},
                            "id"       : {"type": "keyword"},
                            "worker_id": {"type": "keyword"},
                            "location" : {"type": "geo_point"},
                            "sgnl"     : {"type": "integer"}
                        }
                    },
                    "tests"       : {"type": "keyword"}
                }
            }
        }

        # Signal cache index mapping (Version 2)
        self.signals_index_mapping = {
            "mappings": {
                "properties": {
                    "created"  : {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"},
                    "id"       : {"type": "keyword"},
                    "worker_id": {"type": "keyword"},
                    "location" : {"type": "geo_point"},
                    "sgnl"     : {"type": "integer"}
                }
            }
        }

    def process_workers(self, data):
        # Create worker index (if needed)
        self.client.indices.create(index='workers', body=self.worker_index_mapping, ignore=400)
        self.index_requests.append(f"PUT /workers {self.worker_index_mapping}")

        for item in data:
            parser = WifiWorkerParser(item)
            worker_data = parser.get_worker_data()

            # Insert worker data
            worker_index = f"worker_{worker_data['id']}"

            # transform created, updated representations to have a timezone
            worker_created_time = datetime.strptime(worker_data['created'], self.config['DATETIME_FORMAT'])
            worker_data['created'] = worker_created_time.astimezone().isoformat()

            worker_updated_time = datetime.strptime(worker_data['updated'], self.config['DATETIME_FORMAT'])
            worker_data['updated'] = worker_updated_time.astimezone().isoformat()

            worker_doc = {
                **worker_data,
            }

            # Indexes worker document if needed. Otherwise UPDATE.
            self.client.index(index=worker_index, id=worker_data['id'], document=worker_doc, ignore=400)
            self.index_requests.append(f"POST /workers/_doc/{worker_data['id']} {worker_doc}")

            # Create signal index if needed
            signals_index = f"{worker_data['id']}_signals"
            self.client.indices.create(index=signals_index, body=self.signals_index_mapping, ignore=400)
            self.signals_requests.append(f"PUT /{signals_index} {self.signals_index_mapping}")

    def process_signals(self, data):

        for item in data:
            parser = WifiWorkerParser(item)
            worker_data = parser.get_worker_data()
            signal_data = parser.get_signal_data()

            # UPDATE worker data
            worker_index = f"worker_{worker_data['id']}"
            worker_doc = {
                **worker_data,
                # "signal_cache": [
                #     {
                #         "created"  : signal["created"],
                #         "id"       : signal["id"],
                #         "worker_id": signal["worker_id"],
                #         "location" : {"lat": signal["lat"], "lon": signal["lon"]},
                #         "sgnl"     : signal["sgnl"]
                #     } for signal in signal_data
                # ]
            }

            # UPDATE; I don't need the whole doc, just the updated and elapsed time.
            self.client.update(index=worker_index, id=worker_data['id'], doc=worker_doc, ignore=400)

            # Create signal index if needed
            signals_index = f"{worker_data['id']}_signals"

            # Insert the LAST ITEM from signal data, if it's new -- it's added
            for signal in signal_data[:-1]:

                # transform created representation to have a timezone
                signal_created_time = datetime.strptime(signal['created'], self.config['DATETIME_FORMAT'])
                signal['created'] = signal_created_time.astimezone().isoformat()

                signal_doc = {
                    "created"  : signal["created"],
                    "id"       : signal["id"],
                    "worker_id": signal["worker_id"],
                    "location" : {"lat": signal["lat"], "lon": signal["lon"]},
                    "sgnl"     : signal["sgnl"]
                }
                self.client.index(index=signals_index, id=signal["id"], document=signal_doc, ignore=400)
                self.signals_requests.append(f"POST /{signals_index}/_doc/{signal['id']} {signal_doc}")

    def push(self, data):
        try:
            self.process_workers(data)
            self.process_signals(data)
            print(f"Data pushed successfully.")
        except Exception as e:
            print(f"Data push failed: {e}")

        # Save index requests for debugging
        print(f"Exports located @ {self.config['OUTFILE_PATH']}")
        with open(os.path.abspath('.') + "/" + self.config['OUT_FILE'], 'x') as f:
            f.write("\n".join(self.index_requests))

        # with open('/Users/scooper/PycharmProjects/MagPi/src/net/signals_requests.json', 'w') as f:
        #     f.write("\n".join(self.signals_requests))



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
            for signal in self.data.get("signal_cache", [])
        ]

