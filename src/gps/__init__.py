import threading
from flask import Flask
from flask_cors import CORS, cross_origin
import routes
from src.lib.rest_server import RESTServer as RESTServer


class GPSController(threading.Thread):

    def __init__(self):
        super().__init__()

    @staticmethod
    def create_app():
        """Create Flask application."""
        app = Flask('GPS', instance_relative_config=True,
                           subdomain_matching=True)

        cors = CORS(app)
        app.config['CORS_HEADERS'] = 'Content-Type'

        with app.app_context():
            if __name__ == '__main__':
                app.config['SERVER_NAME'] = routes.gpsRet.config['SERVER_NAME']
                app.config['DEBUG'] = routes.gpsRet.config['DEBUG']
                app.register_blueprint(routes.gps_bp)
            return app

    def run(self) -> None:
        try:
            import atexit

            def stop():
                routes.gpsRet.stop()

            atexit.register(stop)

            if __name__ == '__main__':
                RESTServer(self.create_app()).run()

            routes.gpsRet.run()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    GPSController().run()