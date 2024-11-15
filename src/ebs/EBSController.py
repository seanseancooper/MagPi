import threading
from flask import Flask
import routes
from src.lib.rest_server import RESTServer as RESTServer


class EBSController(threading.Thread):

    def __init__(self):
        super().__init__()

    def create_app(self):
        """Create Flask application."""
        app = Flask('EBS',
                    instance_relative_config=True,
                    subdomain_matching=True)

        with app.app_context():
            if __name__ == '__main__':
                app.config['SERVER_NAME'] = routes.ebsMgr.config['EBS']['SERVER_NAME']
                app.config['DEBUG'] = routes.ebsMgr.config['DEBUG']
                app.register_blueprint(routes.ebs_bp)
            return app

    def run(self) -> None:
        try:
            if __name__ == '__main__':
                RESTServer(self.create_app()).run()
            routes.ebsMgr.run()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    EBSController().run()
