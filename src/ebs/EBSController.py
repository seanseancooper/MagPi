import threading
from flask import Flask
from flask_cors import CORS, cross_origin
import routes
from src.lib.rest_server import RESTServer as RESTServer
import logging


class EBSController(threading.Thread):

    def __init__(self):
        super().__init__()

    @staticmethod
    def create_app():
        """Create Flask application."""
        app = Flask('EBS',
                    instance_relative_config=True,
                    subdomain_matching=True)
        cors = CORS(app)
        app.config['CORS_HEADERS'] = 'Content-Type'

        with app.app_context():
            if __name__ == '__main__':
                app.config['SERVER_NAME'] = routes.ebsMgr.config['SERVER_NAME']
                app.config['DEBUG'] = routes.ebsMgr.config['DEBUG']
                app.register_blueprint(routes.ebs_bp)
            return app

    def run(self) -> None:
        if __name__ == '__main__':
            RESTServer(self.create_app()).run()
        routes.ebsMgr.run()


if __name__ == '__main__':
    EBSController().run()
