import os

from src.net.lib.WifiWorkerParser import WifiWorkerParser


class ElasticSearchIntegration:

    def __init__(self):
        self.client = None
        self.operations = []
        self.index_requests = []
        self.signals_requests = []
        self.worker_index_mapping = None
        self.signals_index_mapping = None

    def init(self):

        from elasticsearch import Elasticsearch
        # from getpass import getpass
        # ELASTIC_CLOUD_ID = getpass("Elastic Cloud ID: ")
        # ELASTIC_API_KEY = getpass("Elastic Api Key: ")

        ELASTIC_PASSWORD = "L**_NQ*00Wbbpx24wWqN"

        self.client = Elasticsearch(
                "https://localhost:9200",
                ca_certs="/Users/scooper/PycharmProjects/MagPi/src/map/lib/http_ca.crt",
                basic_auth=("elastic", ELASTIC_PASSWORD)
                # cloud_id=ELASTIC_CLOUD_ID,
                # api_key=ELASTIC_API_KEY,
        )

        if self.client:
            print(f'self.client.info(): {self.client.info()}')

        self.worker_index_mapping = '''
{
    "mappings": {
        "properties": {
            "id"        : {"type": "keyword"},
            "SSID"      : {"type": "keyword"},
            "BSSID"     : {"type": "keyword"},
            "created"   : {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"},
            "updated"   : {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"},
            "elapsed"   : {"type": "date", "format": "HH:mm:ss"},
            "Vendor"    : {"type": "keyword"},
            "Channel"   : {"type": "integer"},
            "Frequency" : {"type": "integer"},
            "Signal"    : {"type": "integer"},
            "Quality"   : {"type": "integer"},
            "Encryption": {"type": "boolean"},
            "is_mute"   : {"type": "boolean"},
            "tracked"   : {"type": "boolean"}
        }
    }
}
        '''

        # nested??
        self.signals_index_mapping = '''
{
  "mappings": {
    "properties": {
      "created": { "type": "date", "format": "yyyy-MM-dd HH:mm:ss" },
      "id": { "type": "keyword" },
      "worker_id": { "type": "keyword" },
      "location": { "type": "geo_point" },
      "sgnl": { "type": "integer" }
    }
  }
}
        '''

    def process(self, data):

        # WORKERS ############################
        worker_index_mapping_curl = f'''PUT /workers''' + self.worker_index_mapping.replace('{', '{{').replace('}', '}}')
        self.index_requests.append(worker_index_mapping_curl)
        self.client.indices.create(index='workers', body=self.worker_index_mapping, ignore=400)

        for _ in data:

            parser = WifiWorkerParser(_)

            worker_data = parser.get_worker_data()
            signal_data = parser.get_signal_data()
            signal_index = f"{worker_data['id']}_signals"

            print(f"worker_{worker_data['id']}:", worker_data)
            print(f"{signal_index}:", signal_data)

            worker_data_curl = f'''
                POST /workers/_doc/worker_{worker_data['id']}
                {{
                  "id": "{worker_data['id']}",
                  "SSID": "{worker_data['SSID']}",
                  "BSSID": "{worker_data['BSSID']}",
                  "created": "{worker_data['created']}",
                  "updated": "{worker_data['updated']}",
                  "elapsed": "{worker_data['elapsed']}",
                  "Vendor": "{worker_data['Vendor']}",
                  "Channel": {worker_data['Channel']},
                  "Frequency": {worker_data['Frequency']},
                  "Signal": {worker_data['Signal']},
                  "Quality": {worker_data['Quality']},
                  "Encryption": {str(worker_data['Encryption']).lower()},
                  "is_mute": {str(worker_data['is_mute']).lower()},
                  "tracked": {str(worker_data['tracked']).lower()}
                }}
            '''

            # index worker doc
            self.index_requests.append(worker_data_curl)
            self.client.index(index=f"worker_{worker_data['id']}", document=worker_data)

            # SIGNALS ############################
            signals_index_mapping_curl = f'''PUT /{signal_index}''' + self.signals_index_mapping.replace('{', '{{').replace('}','}}')
            self.signals_requests.append(signals_index_mapping_curl)
            self.client.indices.create(index=signal_index, body=self.signals_index_mapping, ignore=400)

            for signal in signal_data:
                signal_curl = f'''
                    POST /{signal_index}/_doc/{signal['id']}
                    {{
                      "created": "{signal['created']}",
                      "id": "{str(signal['id'])}",
                      "worker_id": "{signal['worker_id']}",
                      "location": "{signal['lat']}, {signal['lon']}",
                      "sgnl": {signal['sgnl']}
                    }}
                '''

                # index signal doc
                self.signals_requests.append(signal_curl)
                self.client.index(index=signal_index, document=signal)

    def push(self, data):

        try:
            self.process(data)
        except Exception as e:
            print(f'bulk import failed. {e}')

        with open('./index_requests.json', 'w') as f:
            f.write("\n".join(self.index_requests))

        with open('./signals_requests.json', 'w') as f:
            print(os.path.abspath('.'))
            f.write("\n".join(self.signals_requests))
