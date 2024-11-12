import json
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
    """ New MAPAggregator stub to visit module REST contexts, retrieve data,
    'tag' it, and aggregate to a unified defaultdict for the MAP to consume
    via single localized module REST context. """
    def __init__(self):
        super().__init__()
        self.DEBUG = False
        self.config = {}
        self.modules_config = defaultdict(dict)
        self.modules = []
        self.live_modules = []
        self.dead_modules = []
        self.aggregated = defaultdict(str)

        self.retrieving = False
        self.thread = None
        self.result = dict()

    def __str__(self):
        return {f"MAPAggregator: "}

    def configure(self, config_file):
        # read ALL configs; ignore incoming config_file.
        for module_config in sorted(glob.glob(CONFIG_PATH + "/*.json")):
            mod = os.path.basename(module_config).replace('.json', '').upper()
            self.modules.append(mod)
            readConfig(module_config, self.modules_config[mod])

        self.config = self.modules_config['MAP'].copy()

    def register_modules(self):
        """ Register module REST contexts """
        self.live_modules.clear()
        self.dead_modules.clear()

        for mod in self.modules:
            try:
                test = requests.get('http://' + mod.lower() + '.' + self.modules_config[mod]['SERVER_NAME'])
                if test.status_code == 200:
                    self.live_modules.append(mod)
                test.close()
            except Exception:
                self.dead_modules.append(mod)

        # print(f"live modules: {[m for m in self.live_modules]}")
        # print(f"dead modules: {[m for m in self.dead_modules]}")

    def aggregate(self, mod):

        try:
            resp = requests.get('http://' + mod.lower() + '.' + self.modules_config[mod]['SERVER_NAME'])

            if resp.status_code == 200:
                self.aggregated[mod] = json.loads(resp.text)
            else:
                del self.aggregated[mod]  # ??? why not?
            resp.close()
            time.sleep(.5)

        except Exception as e:
            map_logger.warning(f'Aggregator Warning! {e}')

    def stop(self):
        pass

    def run(self):

        self.configure('map.json')
        self.register_modules()

        while self.live_modules:

            for mod in self.live_modules:
                self.aggregate(mod)

            self.register_modules()
            print(f'aggregated: {list(self.aggregated.keys())}')

        print("no running modules!!!")


if __name__ == '__main__':

    mapAgg = MAPAggregator()
    mapAgg.run()