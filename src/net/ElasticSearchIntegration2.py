from elasticsearch import Elasticsearch
import os


class ElasticSearchIntegration:

    def __init__(self):
        self.client = None
        self.operations = []
        self.index_requests = []
        self.signals_requests = []
        self.worker_index_mapping = None
        self.signals_index_mapping = None

    def init(self):
        ELASTIC_PASSWORD = "L**_NQ*00Wbbpx24wWqN"
        self.client = Elasticsearch(
                "https://localhost:9200",
                ca_certs="/Users/scooper/PycharmProjects/MagPi/src/map/lib/http_ca.crt",
                basic_auth=("elastic", ELASTIC_PASSWORD)
        )

        if self.client:
            print(f"Connected to Elasticsearch: {self.client.info()}")

        # Worker index mapping (Version 2)
        self.worker_index_mapping = {
            "mappings": {
                "properties": {
                    "id"          : {"type": "keyword"},
                    "SSID"        : {"type": "keyword"},
                    "BSSID"       : {"type": "keyword"},
                    "created"     : {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"},
                    "updated"     : {"type": "date"},
                    "elapsed"     : {"type": "date"},
                    "Vendor"      : {"type": "keyword"},
                    "Channel"     : {"type": "integer"},
                    "Frequency"   : {"type": "integer"},
                    "Signal"      : {"type": "integer"},
                    "Quality"     : {"type": "integer"},
                    "Encryption"  : {"type": "boolean"},
                    "is_mute"     : {"type": "boolean"},
                    "tracked"     : {"type": "boolean"},
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

    def process(self, data):
        # Create worker index
        self.client.indices.create(index='workers', body=self.worker_index_mapping, ignore=400)
        self.index_requests.append(f"PUT /workers {self.worker_index_mapping}")

        for item in data:
            parser = WifiWorkerParser(item)
            worker_data = parser.get_worker_data()
            signal_data = parser.get_signal_data()

            # Insert worker data
            worker_index = f"worker_{worker_data['id']}"
            worker_doc = {
                **worker_data,
                "signal_cache": [
                    {
                        "created"  : signal["created"],
                        "id"       : signal["id"],
                        "worker_id": signal["worker_id"],
                        "location" : {"lat": signal["lat"], "lon": signal["lon"]},
                        "sgnl"     : signal["sgnl"]
                    } for signal in signal_data
                ]
            }

            # Index worker document
            self.client.index(index=worker_index, id=worker_data['id'], document=worker_doc)
            self.index_requests.append(f"POST /workers/_doc/{worker_data['id']} {worker_doc}")

            # Create signal index (if needed)
            signals_index = f"{worker_data['id']}_signals"
            self.client.indices.create(index=signals_index, body=self.signals_index_mapping, ignore=400)
            self.signals_requests.append(f"PUT /{signals_index} {self.signals_index_mapping}")

            # Insert signal data
            for signal in signal_data:
                signal_doc = {
                    "created"  : signal["created"],
                    "id"       : signal["id"],
                    "worker_id": signal["worker_id"],
                    "location" : {"lat": signal["lat"], "lon": signal["lon"]},
                    "sgnl"     : signal["sgnl"]
                }
                self.client.index(index=signals_index, id=signal["id"], document=signal_doc)
                self.signals_requests.append(f"POST /{signals_index}/_doc/{signal['id']} {signal_doc}")

    def push(self, data):
        try:
            self.process(data)
            print("Data imported successfully.")
        except Exception as e:
            print(f"Bulk import failed: {e}")

        # Save index requests for debugging
        print(os.path.abspath('.'))
        with open('/Users/scooper/PycharmProjects/MagPi/src/net/index_requests.json', 'w') as f:
            f.write("\n".join(self.index_requests))

        with open('/Users/scooper/PycharmProjects/MagPi/src/net/signals_requests.json', 'w') as f:
            f.write("\n".join(self.signals_requests))


# Sample parser (mockup)
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

