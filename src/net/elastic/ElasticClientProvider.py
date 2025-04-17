from elasticsearch import Elasticsearch
from src.config import readConfig

client = None

class ElasticClient:

    def __init__(self):

        self._index_mappings = []
        self.tz = None
        self.config = {}

    def get_client(self, config_file):

        global client
        readConfig(config_file, self.config)

        try:
            client = Elasticsearch(
                    self.config['ELASTIC_HOST'],
                    ca_certs=self.config['ELASTIC_CERT'],
                    basic_auth=(self.config['ELASTIC_USERNAME'], self.config['ELASTIC_PASSWORD']),
            )

            if client:
                print(f"Connected to Elasticsearch: {client.info()}")
                return client
            else:
                print(f"Failed to connect to Elasticsearch. It is online?")

        except ConnectionRefusedError:
            pass
