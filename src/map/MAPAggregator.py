import os
import glob
import threading
from collections import defaultdict
import time
import requests

from src.config import CONFIG_PATH, readConfig

import logging
map_logger = logging.getLogger('gps_logger')


def format_time(_, fmt):
    return f'{_.strftime(fmt)}'


class MAPAggregator(threading.Thread):
    """ MAPAggregator visits module REST contexts, retrieves data, and
    aggregates to a unified defaultdict for the MAP to consume via a
    single localized module REST context.
    """
    def __init__(self):
        super().__init__()
        self.DEBUG = False
        self.config = {}
        self.configs = defaultdict(dict)

        self.modules = []
        self.live_modules = []
        self.dead_modules = []

        self.aggregated = defaultdict(str)

        self.thread = None

    def __str__(self):
        return {f"MAPAggregator: {self.aggregated}"}

    def configure(self, config_file):
        # read ALL configs except controller
        configs = glob.glob(CONFIG_PATH + "/*.json")
        configs.remove(os.path.join(CONFIG_PATH, 'controller.json'))
        configs.remove(os.path.join(CONFIG_PATH, config_file))

        for module_config in configs:
            mod = os.path.basename(module_config).replace('.json', '').upper()
            self.modules.append(mod)
            readConfig(module_config, self.configs[mod])

        readConfig(os.path.join(CONFIG_PATH, config_file), self.config)

    def register_modules(self):
        """ Register 'live' module REST contexts """
        self.live_modules.clear()
        self.dead_modules.clear()

        for mod in self.modules:
            try:
                test = requests.get('http://' + mod.lower() + '.' + self.configs[mod]['SERVER_NAME'])
                if test.ok:
                    self.live_modules.append(mod)
            except Exception:
                self.dead_modules.append(mod)

    def aggregate(self, mod):
        """ collect responses into aggregation """
        try:
            resp = requests.get('http://' + mod.lower() + '.' + self.configs[mod]['SERVER_NAME'])
            if resp.ok:
                self.aggregated[mod] = resp.json()
        except Exception as e:
            map_logger.warning(f'Aggregator Warning! {e}')

    def stop(self):
        pass

    def run(self):

        self.register_modules()

        while True:

            for mod in self.live_modules:
                self.aggregate(mod)

            self.register_modules()

            for mod in self.dead_modules:
                try:
                    self.aggregated.pop(mod)
                except KeyError: pass  # 'missing' is fine.

            print(f'MAPAggregator: {list(self.aggregated.keys())}) live: {[m for m in self.live_modules]} dead: {[m for m in self.dead_modules]}')
            time.sleep(self.config.get('AGGREGATOR_TIMEOUT', .5))


if __name__ == '__main__':
    mapAgg = MAPAggregator()
    mapAgg.configure('map.json')
    mapAgg.run()