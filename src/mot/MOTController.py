import threading
from flask import Flask
from flask_cors import CORS, cross_origin
import routes
from src.lib.rest_server import RESTServer


class MOTController(threading.Thread):

    def __init__(self):
        super().__init__()

    def create_app(self):
        """Create Flask application."""
        app = Flask('MOT',
                    instance_relative_config=True,
                    subdomain_matching=True)
        cors = CORS(app)
        app.config['CORS_HEADERS'] = 'Content-Type'

        with app.app_context():
            if __name__ == '__main__':
                app.config['SERVER_NAME'] = routes.motMgr.config['SERVER_NAME']
                app.config['DEBUG'] = routes.motMgr.config['DEBUG']
                app.register_blueprint(routes.mot_bp)
            return app

    def run(self) -> None:
        try:
            import atexit

            def stop():
                routes.motMgr.stop()

            atexit.register(stop)

            if __name__ == '__main__':
                RESTServer(self.create_app()).run()
            routes.motMgr.run()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    MOTController().run()