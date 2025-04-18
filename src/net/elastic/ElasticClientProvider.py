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
        test = Elasticsearch(
                self.config['ELASTIC_HOST'],
                ca_certs=self.config['ELASTIC_CERT'],
                basic_auth=(self.config['ELASTIC_USERNAME'], self.config['ELASTIC_PASSWORD']),
                max_retries=0,
        )
        if test.ping():
            client = Elasticsearch(
                    self.config['ELASTIC_HOST'],
                    ca_certs=self.config['ELASTIC_CERT'],
                    basic_auth=(self.config['ELASTIC_USERNAME'], self.config['ELASTIC_PASSWORD']),
                    # request_timeout=3.0,
                    # dead_node_backoff_factor=1.0,
                    # max_dead_node_backoff=float,
                    max_retries=2,
                    # retry_on_status=int,
                    # retry_on_timeout=bool,
                    # sniff_on_start =False,
                    # sniff_before_requests=bool,
                    # sniff_on_node_failure=False,
                    # sniff_timeout=float,
                    # min_delay_between_sniffing=float,
                    # timeout=3.0,
                    # sniffer_timeout=float,
                    # sniff_on_connection_fail=bool,
            )

            if client.info():
                print(f"Connected to Elasticsearch: {client.info()}")
                return client
        else:
            print(f"Elasticsearch is offline!")
