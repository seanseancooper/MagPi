import os
import glob
import threading
from collections import defaultdict
import time
from datetime import datetime, timedelta
import requests

from src.config import CONFIG_PATH, readConfig

import logging
map_logger = logging.getLogger('gps_logger')


class MAPAggregator(threading.Thread):
    """ MAPAggregator visits module REST contexts, retrieves data, and
    aggregates to a unified defaultdict for the MAP to consume via a
    single localized module REST context.
    """
    def __init__(self):
        super().__init__()
        self.config = {}
        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()

        self.modules = []
        self.live_modules = []
        self.dead_modules = []

        self.module_configs = defaultdict(dict)
        self.module_data = defaultdict(dict)

        self.iteration = 0
        self.elastic = None

    def stop(self):
        print(f'stopping.')

    def configure(self, config_file, **kwargs):

        non_config_files = kwargs.get('non_config_files')
        non_config_files.extend([os.path.basename(config_file)])
        config_files = glob.glob(CONFIG_PATH + "/*.json")
        [config_files.remove(CONFIG_PATH + '/' + non_config) for non_config in non_config_files]

        readConfig(config_file, self.config)

        for module_config in config_files:
            mod = os.path.basename(module_config).replace('.json', '')
            self.modules.append(mod)
            readConfig(os.path.basename(module_config), self.module_configs[mod])

        self.elastic = ElasticSearchIntegration()
        self.elastic.init()

    def register_modules(self):
        """ discover 'live' module REST contexts """
        self.live_modules.clear()
        self.dead_modules.clear()

        def test(m):
            try:
                test = requests.get('http://' + m + '.' + self.module_configs[m]['SERVER_NAME'])
                if test.ok:
                    self.live_modules.append(m)
            except Exception:
                self.dead_modules.append(m)

        [test(mod) for mod in self.modules]

    def aggregate(self, mod):
        """ collect responses into aggregation """
        try:
            data = requests.get('http://' + mod + '.' + self.module_configs[mod]['SERVER_NAME'])
            if data.ok:
                self.module_data[mod] = data.json()
                if self.elastic:
                    self.elastic.push(self.module_data[mod])
        except Exception as e:
            map_logger.warning(f'Data Aggregator Warning [{mod}]! {e}')

    def run(self):

        self.register_modules()

        while True:
            self.iteration += 1
            self.updated = datetime.now()
            self.elapsed = self.updated - self.created

            for mod in self.live_modules:
                self.aggregate(mod)

            self.register_modules()

            for mod in self.dead_modules:
                try:
                    self.module_data[mod] = {}
                except KeyError: pass  # 'missing' is fine.

            time.sleep(self.config.get('AGGREGATOR_TIMEOUT', .5))


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


# Install Docker:
#   docker network create elastic
#   docker pull docker.elastic.co/elasticsearch/elasticsearch:8.17.2
#   docker pull docker.elastic.co/kibana/kibana:8.17.2

# docker run --name es01 --net elastic -p 9200:9200 -it -m 1GB docker.elastic.co/elasticsearch/elasticsearch:8.17.2
# docker run --name kib01 --net elastic -p 5601:5601 docker.elastic.co/kibana/kibana:8.17.2

# https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ✅ Elasticsearch security features have been automatically configured!
# ✅ Authentication is enabled and cluster connections are encrypted.
#
# ℹ️  Password for the elastic user (reset with `bin/elasticsearch-reset-password -u elastic`):
#   L**_NQ*00Wbbpx24wWqN
#
# ℹ️  HTTP CA certificate SHA-256 fingerprint:
#   9022782a7780c081f54194ce37726141fa7f77157d4b7a42565037aceda242d7
#
# ℹ️  Configure Kibana to use this cluster:
# • Run Kibana and click the configuration link in the terminal when Kibana starts.
# • Copy the following enrollment token and paste it into Kibana in your browser (valid for the next 30 minutes):
#   eyJ2ZXIiOiI4LjE0LjAiLCJhZHIiOlsiMTcyLjE4LjAuMjo5MjAwIl0sImZnciI6IjkwMjI3ODJhNzc4MGMwODFmNTQxOTRjZTM3NzI2MTQxZmE3Zjc3MTU3ZDRiN2E0MjU2NTAzN2FjZWRhMjQyZDciLCJrZXkiOiI2MGMtZ3BVQm9CcDdGcUc3aWlVTzpNS3ZtU0I5eFJBMjZhQk0xMWUtY0t3In0=
#
# ℹ️ Configure other nodes to join this cluster:
# • Copy the following enrollment token and start new Elasticsearch nodes with `bin/elasticsearch --enrollment-token <token>` (valid for the next 30 minutes):
#   eyJ2ZXIiOiI4LjE0LjAiLCJhZHIiOlsiMTcyLjE4LjAuMjo5MjAwIl0sImZnciI6IjkwMjI3ODJhNzc4MGMwODFmNTQxOTRjZTM3NzI2MTQxZmE3Zjc3MTU3ZDRiN2E0MjU2NTAzN2FjZWRhMjQyZDciLCJrZXkiOiI3VWMtZ3BVQm9CcDdGcUc3aWlYNzppX1pQR0lYS1I4LWNNY0pCbk9rZ0tRIn0=
#
#   If you're running in Docker, copy the enrollment token and run:
#   `docker run -e "ENROLLMENT_TOKEN=<token>" docker.elastic.co/elasticsearch/elasticsearch:8.17.2`
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# regenerate credentials
#   docker exec -it es01 /usr/share/elasticsearch/bin/elasticsearch-reset-password -u elastic
#   docker exec -it es01 /usr/share/elasticsearch/bin/elasticsearch-create-enrollment-token -s kibana

# We recommend storing the elastic password as an environment variable in your shell. Example:
#   export ELASTIC_PASSWORD="L**_NQ*00Wbbpx24wWqN"

# https://www.elastic.co/guide/en/elasticsearch/reference/current/security-basic-setup.html
# https://www.elastic.co/guide/en/elasticsearch/reference/current/security-basic-setup-https.html

# copy cert to local machine:
# docker cp es01:/usr/share/elasticsearch/config/certs/http_ca.crt .

# https://www.elastic.co/guide/en/enterprise-search-clients/python/current/connecting.html#connect-self-hosted
# https://www.elastic.co/guide/en/kibana/current/asset-tracking-tutorial.html



# valid ways of moving the data:
# - do ETL on JSON: extract worker and signals in MapAggregator component; push to Elastic.  [BLOCKING?]
#
# + Have the workers DUMP THE DATA ON EXIT (worker.stop() dumps only tracked items)); THEN push to Elastic.

#       DECORATE append_to_outfile in wifi_utils. have this be the elastic integration point.
#       [NOCARE, ONLY TRACKED ITEMS (+), includes 4/6 (not files) and solves 'when?']
#       indexes can be managed atomically. we can programmatically expunge signals and keep workers.

# - signals and workers use methods to make client calls in real-time; push to Elastic. [BLOCKING?, maintainence]
# - tight coupling to tracked objects; push to Elastic. [WHEN PUSHED? WHAT IS USEFUL ABOUT NON-TRACKED ITEMS?]

# > use a logstash http_polling connector and a mapping; poll module endpoints; pull to Elastic.
# - import files; pull to Elastic.
#
# A. IS THE CODE BLOCKING?
# B. What if Elastic is 'offline'; how does this affect the following use cases?
#       Module users, real-time (signals): not affected unless code is blocking!
#       Apparatus Users, real-time (map+signals)
#           OFFLINE  ANYWAY:
#               Ingest processes, continuity of data. availability, stability of components, decoupling
#               Kibana dashboards are offline, but not affecting module/apparatus users...
#               ML predictions, offline analysis
#       Maintainability
#
# Which is fastest and easiest to implement, so we can discover mistakes fast and correct them?
#
# ETC, Which offers the most downstream flexibility if needed to change.
# {"message": "", "48:9B:D5:F7:E2:C0": {"SSID": "CCOB_Library", "BSSID": "48:9B:D5:F7:E2:C0", "created": "13:47:44", "updated": "14:40:37", "elapsed": "00:52:05", "Vendor": "Extreme Networks Headquarters", "Channel": 1, "Frequency": 1281, "Signal": -99, "Quality": 24, "Encryption": false, "is_mute": false, "tracked": true, "signal_cache": [{"datetime": "2025-03-04 14:40:13.226561", "id": "54827a9e-49fc-482b-a46c-97f8262dccff", "lon": -105.068295, "lat": 39.916938, "sgnl": -99}, {"datetime": "2025-03-04 14:40:17.974622", "id": "f0a9b88b-78a2-48f3-ba16-708ffe507ad3", "lon": -105.068486, "lat": 39.916797, "sgnl": -99}, {"datetime": "2025-03-04 14:40:22.764689", "id": "1176761b-9e3c-434b-8e8d-58c1be094650", "lon": -105.068668, "lat": 39.916763, "sgnl": -99}, {"datetime": "2025-03-04 14:40:32.639993", "id": "573c5000-e9c6-4a05-87b9-41305449f3b1", "lon": -105.06867, "lat": 39.916891, "sgnl": -99}, {"datetime": "2025-03-04 14:40:37.499255", "id": "72dcbdbf-8d6c-4d20-9ac2-da809864e0c8", "lon": -105.068617, "lat": 39.916906, "sgnl": -99}], "tests": []}}

# if it doesn't exist, create a single index for all workers


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


if __name__ == '__main__':
    mapAgg = MAPAggregator()
    mapAgg.configure('map.json')
    mapAgg.run()
