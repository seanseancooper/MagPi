import os
from flask import Flask

import src.arx.__init__ as arx
import src.gps.__init__ as gps
import src.wifi.__init__ as wifi
import src.cam.__init__ as cam

import __init__ as root
configuration = {}


def configure():
    from src.config import readConfig, CONFIG_PATH
    readConfig(os.path.join(CONFIG_PATH, 'controller.json'), configuration)


def return_app_ctx():

    app = Flask(__name__, instance_relative_config=True)
    app.config['SERVER_NAME'] = configuration['SERVER_NAME']

    root.root_bp.register_blueprint(arx.arx_bp)
    root.root_bp.register_blueprint(cam.cam_bp)
    root.root_bp.register_blueprint(gps.gps_bp)
    root.root_bp.register_blueprint(wifi.wifi_bp)
    app.register_blueprint(root.root_bp)

    return app


if __name__ == '__main__':

    configure()
    webapp = return_app_ctx()
    webapp.run()
