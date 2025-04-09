import os
import glob
import threading
from collections import defaultdict
import time
from datetime import datetime, timedelta
import requests

from src.net.ElasticSearchIntegration import ElasticSearchIntegration

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

        # self.elastic = ElasticSearchIntegration()
        # self.elastic.configure()

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
                # if self.elastic:
                #     self.elastic.push(self.module_data[mod])
                #     self.elastic.pull(mod)
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


if __name__ == '__main__':
    mapAgg = MAPAggregator()
    mapAgg.configure('map.json')
    mapAgg.run()
