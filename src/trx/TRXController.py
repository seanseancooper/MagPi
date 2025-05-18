import threading
from flask import Flask
from flask_cors import CORS
import routes
from src.net.FlaskRESTServer import RESTServer


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
                app.config['SERVER_NAME'] = routes.trxRet.config['SERVER_NAME']
                app.config['DEBUG'] = routes.trxRet.config['DEBUG']
                app.register_blueprint(routes.trx_bp)
            return app

    def run(self) -> None:
        try:
            import atexit

            def stop():
                routes.scanner.stop()

            atexit.register(stop)

            if __name__ == '__main__':
                RESTServer(self.create_app()).run()

            routes.scanner.run()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    TRXController().run()