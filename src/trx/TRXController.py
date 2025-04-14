import threading
from flask import Flask
from flask_cors import CORS, cross_origin
import routes
from src.lib.rest_server import RESTServer


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
                app.config['SERVER_NAME'] = routes.trxProd.config['SERVER_NAME']
                app.config['DEBUG'] = routes.trxProd.config['DEBUG']
                app.register_blueprint(routes.trx_bp)
            return app

    def run(self) -> None:
        try:
            import atexit

            def stop():
                routes.trxProd.stop()

            atexit.register(stop)

            if __name__ == '__main__':
                RESTServer(self.create_app()).run()

                t = threading.Thread(target=routes.trxProd.retriever.run)
                t.start()

            routes.trxProd.run()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    TRXController().run()