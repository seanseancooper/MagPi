import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
from src.config import readConfig
import requests

class ViewContainer(threading.Thread):

    def __init__(self):
        super().__init__()
        self.config = {}
        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()

        self.modules = []
        self.module_tabs = []

        self.module_stats = defaultdict()
        self.module_configs = defaultdict()

        self.title = None

    def stop(self):
        print(f'stopping.')

    def configure(self, config_file):
        readConfig(config_file, self.config)
        self.modules = self.config.get('MODULES')
        _modules = self.config.get('MODULE_TABS')

        for _mod in _modules.items():
            _m, _conf = _mod
            for _tab in _conf.items():
                # a, b = _tab
                # self.module_tabs.append(ViewContainerTab(a, b))
                self.module_tabs.append(_tab)

        self.title = f"ViewContainer: {[mod.upper() for mod in self.modules]}"

    def add_module(self, m):
        self.modules.append(m)
        print(f'added module {m}')

    def get_module_stats(self, mod):
        """ return all stats """
        try:
            resp = requests.get(f'http://map.localhost:5005/stats/{mod}')
            if resp.ok:
                self.module_stats[mod] = resp.json()
                return self.module_stats[mod]
        except Exception as e:
            print(f'ViewContainer failed to get aggregated statistics for {mod}: {e}')

    def get_module_config(self, mod):
        """ return all config """
        try:
            resp = requests.get(f'http://map.localhost:5005/config/{mod}')
            if resp.ok:
                self.module_configs[mod] = resp.json()
                return self.module_configs[mod]
        except Exception as e:
            self.module_tabs.pop(mod)
            print(f'ViewContainer failed to aggregate configuration for {mod}: {e}')

    def get_stat_for_module(self, m, stat):
        """ return a specific value from stats """
        try:
            self.get_module_stats(m)
            value = self.module_stats[m].get(stat) or 'offline'
            return value
        except KeyError:
            return 'unknown'

    def del_module(self, m):
        self.modules.remove(m)
        print(f'removed module {m}')

    @staticmethod
    def get_view_container(app):

        with app.app_context():
            from flask import g
            if "viewcontainer" not in g:
                g.viewcontainer = ViewContainer()
            return g.viewcontainer

    def run(self):
        while True:
            self.updated = datetime.now()
            self.elapsed = self.updated - self.created
            time.sleep(1)
            pass


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
