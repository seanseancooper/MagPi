import threading
from flask import Flask
from flask_cors import CORS, cross_origin
import routes
from src.lib.rest_server import RESTServer as RESTServer


class ARXController(threading.Thread):

    def __init__(self):
        super().__init__()

    @staticmethod
    def create_app():
        """Create Flask application."""
        app = Flask('arx',
                    instance_relative_config=True,
                    subdomain_matching=True)

        cors = CORS(app)
        app.config['CORS_HEADERS'] = 'Content-Type'

        with app.app_context():
            if __name__ == '__main__':
                app.config['SERVER_NAME'] = routes.arxRec.config['SERVER_NAME']
                app.config['DEBUG'] = routes.arxRec.config['DEBUG']
                app.register_blueprint(routes.arx_bp)
            return app

    def run(self) -> None:
        try:
            import atexit

            def stop():
                routes.arxRec.stop()  # required.

            atexit.register(stop)

            if __name__ == '__main__':
                RESTServer(self.create_app()).run()
            routes.arxRec.run()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    ARXController().run()
