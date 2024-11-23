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
        self.config = {}

    def stop(self):
        print(f'stopping.')
        pass

    def configure(self, config_file):
        readConfig(config_file, self.config)

    @staticmethod
    def get_scanner(app):

        with app.app_context():
            from flask import g
            if "scanner" not in g:
                g.scanner = ViewContainer()
            return g.scanner

    def run(self):
        while True:
            self.updated = datetime.now()
            self.elapsed = datetime.now() - self.created
            time.sleep(1)
            pass

