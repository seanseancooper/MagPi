import threading
from flask import Flask
import __init__
from src.lib.rest_server import RESTServer as RESTServer


class MOTController(threading.Thread):

    def __init__(self):
        super().__init__()

    def create_app(self):
        """Create Flask application."""
        app = Flask('MOT',
                    instance_relative_config=True,
                    subdomain_matching=True)

        with app.app_context():
            if __name__ == '__main__':
                app.config['SERVER_NAME'] = __init__.motMgr.config['MOT']['SERVER_NAME']
                app.config['DEBUG'] = __init__.motMgr.config['DEBUG']
                app.register_blueprint(__init__.mot_bp)
            return app

    def run(self) -> None:
        try:
            if __name__ == '__main__':
                RESTServer(self.create_app()).run()
            __init__.motMgr.run()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    MOTController().run()