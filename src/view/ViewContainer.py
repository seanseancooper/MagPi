import os
import glob
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
import requests

from src.config import readConfig, CONFIG_PATH
from src.lib.utils import format_time, format_delta

import logging

view_logger = logging.getLogger('view_logger')
speech_logger = logging.getLogger('speech_logger')


class ViewContainer(threading.Thread):

    def __init__(self):
        super().__init__()
        self.config = {}
        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()

        self.live_modules = []
        self.dead_modules = []

        self.modules = []
        self.module_tabs = []

        self.module_stats = defaultdict(dict)
        self.module_configs = defaultdict(dict)
        self.module_data = defaultdict(dict)

        self.title = None
        self.iteration = 0

    def stop(self):
        print(f'stopping.')

    def configure(self, config_file, **kwargs):

        non_config_files = kwargs.get('non_config_files')
        non_config_files.extend([os.path.basename(config_file)])
        config_files = glob.glob(CONFIG_PATH + "/*.json")
        [config_files.remove(CONFIG_PATH + '/' + non_config) for non_config in non_config_files]

        readConfig(config_file, self.config)  # expressly NOT in modules OR module_configs

        for module_config in config_files:
            mod = os.path.basename(module_config).replace('.json', '')

            self.modules.append(mod)
            readConfig(os.path.basename(module_config), self.module_configs[mod])

            _module_tabs = self.config.get('MODULE_TABS')

            if mod not in ['gps']:
                for tup in _module_tabs[mod].items():
                    _tab, _tab_time = tup
                    # self.module_tabs.append(ViewContainerTab(_tab, _time))
                    self.module_tabs.append(tup)

        self.title = f"MagPi ViewContainer: {[mod.upper() for mod in self.modules]}"

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
        """ collect data and stats into aggregation """
        try:
            data = requests.get('http://' + mod + '.' + self.module_configs[mod]['SERVER_NAME'])
            if data.ok:
                self.module_data[mod] = data.json()
        except Exception as e:
            view_logger.warning(f'Data Aggregator Warning [{mod}]! {e}')

        try:
            stats = requests.get('http://' + mod + '.' + self.module_configs[mod]['SERVER_NAME'] + '/stats')
            if stats.ok:
                self.module_stats[mod] = stats.json()  # current module stats
        except Exception as e:
            view_logger.warning(f'Statistics Aggregator Warning [{mod}]! {e}')

    def get_module_stats(self, mod):
        """ return all stats """
        return self.module_stats[mod]

    def get_module_config(self, mod):
        """ return all config """
        return self.module_configs[mod]

    def get_stat_for_module(self, m, stat):
        """ return a specific value from stats """
        # self.reload(m)
        value = self.module_stats[m].get(stat) or 'offline'
        return value

    def reload(self, mod):
        """ reload specific module """
        self.unload(mod)
        self.aggregate(mod)
        print(f'reloaded {mod}')
        return True

    def unload(self, unload):
        """ unload a specific module, auto reload on next pass """

        copy = self.module_data.copy()
        self.module_data.clear()

        def add_module(mod):
            self.module_data[mod] = copy[mod]

        [add_module(mod) for mod in copy if mod != unload]

        print(f'unloaded {unload}')
        return True

    @staticmethod
    def get_view_container(app):

        with app.app_context():
            from flask import g
            if "viewcontainer" not in g:
                g.viewcontainer = ViewContainer()
            return g.viewcontainer

    def report(self):

        def module_info(m):

            updated = '--:--:--'
            elapsed = '--:--:--'  # needs reset to 0 on restart

            try:
                updated = self.module_stats[m]['updated']
                elapsed = self.module_stats[m]['elapsed']
            except KeyError:
                pass

            messaging = m + " "

            if m in self.live_modules:
                messaging += '\033[32monline\033[0m: ' + elapsed + ' '

            if m in self.dead_modules:
                messaging += '\033[31moffline\033[0m: ' + updated + ' '

            return messaging

        if self.iteration % 10 == 0:
            print(f"MAPAggregator [{self.iteration}] {format_delta(self.elapsed, '%H:%M:%S')} elapsed")
            # yell about offline modules
            # [speech_logger.info(f'{mod} offline.') for mod in self.dead_modules]

        [print(module_info(mod), end='') for mod in self.modules if mod != 'view']
        print('')

    def run(self):

        self.register_modules()
        # speech_logger.info('aggregator started')

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

            self.report()
            time.sleep(self.config.get('AGGREGATOR_TIMEOUT', .5))


class ViewContainerTab:

    # create tabs and put ViewContainerTab in self.module_tabs
    def __init__(self, tab, view_timeout):
        super().__init__()

        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()
        self.view_timeout = view_timeout
        self.module = None
        self.tab = tab

    def get_tab(self, module_tabs):
        return [tab.split(':')[0] for tab in module_tabs if tab is self.module]

    def get_timeout(self, module_tabs):
        return [tab.split(':')[1] for tab in module_tabs if tab is self.module]
