import threading
from flask import Flask
from flask_cors import CORS, cross_origin
import src.cam.routes as routes
from src.lib.rest_server import RESTServer


class CAMController(threading.Thread):

    def __init__(self):
        super().__init__()

    @staticmethod
    def create_app():
        """Create Flask application."""
        app = Flask('CAM',
                    instance_relative_config=True,
                    subdomain_matching=True)

        cors = CORS(app)
        app.config['CORS_HEADERS'] = 'Content-Type'

        with app.app_context():
            if __name__ == '__main__':
                app.config['SERVER_NAME'] = routes.camMgr.config['SERVER_NAME']
                app.config['DEBUG'] = routes.camMgr.config['DEBUG']
                app.register_blueprint(routes.cam_bp)
            return app

    def run(self) -> None:
        try:
            import atexit

            def stop():
                routes.camMgr.stop()

            atexit.register(stop)

            if __name__ == '__main__':
                RESTServer(self.create_app()).run()

            routes.camMgr.run()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    CAMController().run()
