import threading
import logging.handlers

from src.config import readConfig

logger_root = logging.getLogger('root')


class RESTServer(threading.Thread):

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.configuration = {}

    def configure(self):
        readConfig(f'{self.app.name.lower()}.json', self.configuration)

    def run(self):

        self.configure()

        try:
            if self.app.config['SERVER_NAME'] is None:
                self.app.config['SERVER_NAME'] = self.configuration['SERVER_NAME']
                self.app.config['DEBUG'] = self.configuration['DEBUG'] #TODO:does this work?
            threading.Thread(target=self.app.run, name='RestService', daemon=True).start()
            logger_root.info(f"[RESTServer]: starting HTTP service for {self.app.name}")
        except Exception as e:
            logger_root.error(f"[RESTServer]: HTTP service streaming error on {self.app.name}: {str(e)}")

