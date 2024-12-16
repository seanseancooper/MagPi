import threading
import time
from datetime import datetime, timedelta
from src.config import readConfig


class ViewContainer(threading.Thread):

    def __init__(self):
        super().__init__()

        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()
        self.view_timeout = 0
        self.modules = ['wifi', 'trx']

        # read fragments in module templates dir.
        # fragment name is module_tab
        # templates/
        #   post    <-- anything before any fragment (js or html)
        #   pre     <-- anything after any fragment (js only)
        #   wifi.j2    <-- the fragment (js+html)
        #   tracked.j2
        #   ghosts.j2

        self.module_tabs = {
                                'wifi': ['wifi', 'tracked', 'ghosts'],
                                'trx': ['trx']
                            }

        self.config = {}

    def stop(self):
        print(f'stopping.')

    def configure(self, config_file):
        readConfig(config_file, self.config)
        self.view_timeout = self.config.get('VIEW_TIMEOUT')

    def add_module(self, m):
        self.modules.append(m)
        print(f'added module {m}')

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
            self.elapsed = datetime.now() - self.created
            time.sleep(1)
            pass

