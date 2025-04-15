import threading
from flask import Flask
from flask_cors import CORS, cross_origin
import routes
from src.lib.rest_server import RESTServer


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
                app.config['SERVER_NAME'] = routes.mapAgg.config['SERVER_NAME']
                app.config['DEBUG'] = routes.mapAgg.config['DEBUG']
                app.register_blueprint(routes.map_bp)
            return app

    def run(self) -> None:
        try:
            import atexit

            def stop():
                routes.mapAgg.stop()

            atexit.register(stop)

            if __name__ == '__main__':
                RESTServer(self.create_app()).run()

            import os
            os.chdir('src/')
            if routes.mapAgg.config['NODE_BUILD'] is True:
                routes.node.build()

            # start elastic instance/cluster docker container.

            # start the map node services on :5173
            routes.node.run()
            routes.mapAgg.run()

        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    MAPController().run()