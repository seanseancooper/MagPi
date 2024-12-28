import os
import glob
import threading
from collections import defaultdict
import time
from datetime import datetime, timedelta
import requests

from src.config import CONFIG_PATH, readConfig
from src.lib.utils import format_delta

import logging
map_logger = logging.getLogger('gps_logger')
speech_logger = logging.getLogger('speech_logger')


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
        self.iteration = 0
        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()

        self.modules = []
        self.module_stats = {}
        self.live_modules = []
        self.dead_modules = []

        self.aggregated = defaultdict(str)  # a string representation of the dict.

        self.thread = None

    def __str__(self):
        return f"MAPAggregator: {self.aggregated}"

    def configure(self, config_file, **kwargs):
        non_config_files = kwargs.get('non_config_files')
        # no need now for 'view'
        non_config_files.extend([os.path.basename(config_file), 'view.json'])
        configs = glob.glob(CONFIG_PATH + "/*.json")
        [configs.remove(CONFIG_PATH + '/' + non_config) for non_config in non_config_files]

        for module_config in configs:
            mod = os.path.basename(module_config).replace('.json', '')
            self.modules.append(mod)
            self.module_stats[mod] = {'created': '',
                                      'updated': '',
                                      'elapsed': ''}
            readConfig(os.path.basename(module_config), self.configs[mod])

        readConfig(config_file, self.config)

    def start_module(self, mod):
        ''' start module in modules '''
        print(f'started module: {mod}')

    def register_modules(self):
        """ discover 'live' module REST contexts """
        self.live_modules.clear()
        self.dead_modules.clear()

        def test(m):
            try:
                test = requests.get('http://' + m + '.' + self.configs[m]['SERVER_NAME'])
                if test.ok:
                    self.live_modules.append(m)
            except Exception:
                self.dead_modules.append(m)

        [test(mod) for mod in self.modules]

    def aggregate(self, mod):
        """ collect responses into aggregation """
        try:
            conf = requests.get('http://' + mod + '.' + self.configs[mod]['SERVER_NAME'])
            if conf.ok:
                self.aggregated[mod] = conf.json()
        except Exception as e:
            map_logger.warning(f'Configuration Aggregator Warning [{mod}]! {e}')

        try:
            stats = requests.get('http://' + mod + '.' + self.configs[mod]['SERVER_NAME'] + '/stats')
            if stats.ok:
                self.module_stats[mod] = stats.json()  # current module stats
        except Exception as e:
            map_logger.warning(f'Statistics Aggregator Warning [{mod}]! {e}')

    def report(self):

        def module_info(m):
            created = self.module_stats[m]['created']
            elapsed = self.module_stats[m]['elapsed']
            messaging = m + " "

            if m in self.live_modules:
                messaging += '\033[32monline\033[0m: ' + elapsed + ' '

            if m in self.dead_modules:
                messaging += '\033[31moffline\033[0m: ' + created + ' '

            return messaging

        if self.iteration % 10 == 0:
            print(f"MAPAggegator [{self.iteration}] {format_delta(self.elapsed, "%H:%M:%S")} elapsed")
            # yell about offline modules
            [speech_logger.info(f'{mod} offline.') for mod in self.dead_modules]

        [print(module_info(mod), end='') for mod in self.modules]
        print('')

    def reload(self, mod):
        """ reload specific module """
        self.unload(mod)
        self.aggregate(mod)
        print(f'reloaded {mod}')
        return True

    def unload(self, unload):
        """ unload a specific module, auto reload on next pass """

        copy = self.aggregated.copy()
        self.aggregated.clear()

        def add_module(mod):
            self.aggregated[mod] = copy[mod]

        [add_module(mod) for mod in copy if mod != unload]

        print(f'unloaded {unload}')
        return True

    def stop(self):
        pass

    def run(self):

        self.register_modules()
        speech_logger.info('aggregator started')

        while True:
            self.iteration += 1
            self.updated = datetime.now()
            self.elapsed = self.updated - self.created

            for mod in self.live_modules:
                self.aggregate(mod)

            self.register_modules()

            for mod in self.dead_modules:
                try:
                    self.aggregated.pop(mod)
                except KeyError: pass  # 'missing' is fine.

            self.report()

            time.sleep(self.config.get('AGGREGATOR_TIMEOUT', .5))


if __name__ == '__main__':
    mapAgg = MAPAggregator()
    mapAgg.configure('map.json')
    mapAgg.run()
