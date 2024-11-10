import threading
from flask import Flask
from flask_cors import CORS, cross_origin
import __init__
from src.lib.rest_server import RESTServer as RESTServer


class TRXController(threading.Thread):

    def __init__(self):
        super().__init__()

    @staticmethod
    def create_app():
        """Create Flask application."""
        app = Flask('TRX', instance_relative_config=True,
                           subdomain_matching=True)

        cors = CORS(app)
        app.config['CORS_HEADERS'] = 'Content-Type'

        with app.app_context():
            if __name__ == '__main__':
                app.config['SERVER_NAME'] = __init__.trxRet.config['SERVER_NAME']
                app.config['DEBUG'] = __init__.trxRet.config['DEBUG']
                app.register_blueprint(__init__.trx_bp)
            return app

    def run(self) -> None:
        try:
            if __name__ == '__main__':
                RESTServer(self.create_app()).run()

            __init__.trxRet.run()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    TRXController().run()