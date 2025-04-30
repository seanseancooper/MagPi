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
                routes.gpsRet.stop()
                routes.map_node.stop()
                routes.gps_node.stop()

            atexit.register(stop)

            if __name__ == '__main__':
                RESTServer(self.create_app()).run()

            import os

            if routes.map_node.config['NODE_BUILD'] is True:
                os.chdir('src/')
                routes.map_node.build()
                os.chdir('../')

            if routes.mapAgg.config['NODE_BUILD'] is True:
                os.chdir('js_gps_ret/')
                routes.gps_node.build()
                os.chdir('../')

            # start elastic instance/cluster docker container.

            # run the map node services on :5173
            os.chdir('src/')
            routes.map_node.run()
            os.chdir('../')

            # run the js_gps retrieval services on :5014
            os.chdir('js_gps_ret/')
            routes.gps_node.run()
            os.chdir('../')

            # start() the gps retrieval service on :5005
            routes.gpsRet.run()
            # run() the map aggregator service on :5005
            routes.mapAgg.run()

        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    MAPController().run()