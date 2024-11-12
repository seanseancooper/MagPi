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
    via single localized module REST context.

    This will not update the aggregation if the module goes offline!

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
                if test.status_code == 200 or 302:
                    self.live_modules.append(mod)
                test.close()
            except Exception:
                self.dead_modules.append(mod)

    def aggregate(self, mod):

        try:
            resp = requests.get('http://' + mod.lower() + '.' + self.configs[mod]['SERVER_NAME'])

            if resp.status_code == 200 or 302:
                self.aggregated[mod] = json.loads(resp.text)
            else:
                try:
                    del self.aggregated[mod]  # can't remove?! this will not update if module goes offline!
                except Exception as e:
                    map_logger.warning(f'Aggregator Warning! Module resolution failed {mod}: {e}')

            resp.close()
            time.sleep(self.config.get('AGGREGATOR_TIMEOUT', .5))

        except Exception as e:
            map_logger.warning(f'Aggregator Warning! {e}')

    def stop(self):
        pass

    def run(self):

        self.register_modules()

        while self.live_modules:

            for mod in self.live_modules:
                self.aggregate(mod)

            self.register_modules()
            print(f'aggregated: {list(self.aggregated.keys())}) live: {[m for m in self.live_modules]} dead: {[m for m in self.dead_modules]}')

        map_logger.warning("no running modules!!!")


if __name__ == '__main__':
    mapAgg = MAPAggregator()
    mapAgg.configure('map.json')
    mapAgg.run()