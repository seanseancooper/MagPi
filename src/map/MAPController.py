import threading
import time

from flask import Flask
from flask_cors import CORS, cross_origin
import __init__
from src.lib.rest_server import RESTServer as RESTServer


class MAPController(threading.Thread):

    def __init__(self):
        super().__init__()

    @staticmethod
    def create_app():
        """Create Flask application."""
        app = Flask('MAP', instance_relative_config=True,
                           subdomain_matching=True)

        cors = CORS(app)
        app.config['CORS_HEADERS'] = 'Content-Type'

        with app.app_context():
            if __name__ == '__main__':
                app.config['SERVER_NAME'] = __init__.config['SERVER_NAME']
                app.config['DEBUG'] = __init__.config['DEBUG']
                app.register_blueprint(__init__.map_bp)
            return app

    def run(self) -> None:
        try:
            if __name__ == '__main__':
                RESTServer(self.create_app()).run()

            import os
            os.chdir('src/')
            #TODO: run the build command, but don't start the server
            # ✓ built in 3.28s... takes a second.
            __init__.node.run()

            while True:  # perhaps log requests?
                time.sleep(1)
                pass

        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    MAPController().run()