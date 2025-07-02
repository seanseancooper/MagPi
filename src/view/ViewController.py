import threading
from flask import Flask
from flask_cors import CORS
import routes as view
from src.net.FlaskRESTServer import RESTServer as RESTServer


class ViewController(threading.Thread):

    def __init__(self):
        super().__init__()

    @staticmethod
    def create_app():
        """Create Flask application."""
        app = Flask('view',
                    instance_relative_config=True,
                    subdomain_matching=True)

        cors = CORS(app)
        app.config['CORS_HEADERS'] = 'Content-Type'

        with app.app_context():
            if __name__ == '__main__':
                app.config['SERVER_NAME'] = view.viewContainer.config['SERVER_NAME']
                app.config['DEBUG'] = view.viewContainer.config['DEBUG']
                view.viewContainer.viewcontainer = view.viewContainer.get_view_container(app)
                app.register_blueprint(view.vc_bp)
            return app

    def run(self) -> None:
        try:
            import atexit

            def stop():
                view.viewContainer.stop()

            atexit.register(stop)

            if __name__ == '__main__':
                RESTServer(self.create_app()).run()
            view.viewContainer.run()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    ViewController().run()