import os
import threading
import importlib
from flask import Flask
import atexit


from src.lib.rest_server import RESTServer
import src.arx.ARXController as ARXController
import src.gps.GPSController as GPSController
import src.wifi.WIFIController as WIFIController
import src.cam.CAMController as CAMController

import src.arx.__init__ as arx
import src.gps.__init__ as gps
import src.wifi.__init__ as wifi
import src.cam.__init__ as cam


import __init__ as root
configuration = {}


def configure():
    from src.config import readConfig, CONFIG_PATH
    readConfig(os.path.join(CONFIG_PATH, 'controller.json'), configuration)


def load_modules(modconfig):
    m, bp, controller, runmethod, stopmethod = modconfig.split(':')

    # import module m
    mdle = importlib.import_module(m)

    # BROKEN: start() the app controller.
    threading.Thread(target=mdle.WIFIController.WifiController.run, daemon=True).start()


def return_app_ctx():

    app = Flask(__name__, instance_relative_config=True)
    app.config['SERVER_NAME'] = configuration['SERVER_NAME']

    root.root_bp.register_blueprint(arx.arx_bp)
    root.root_bp.register_blueprint(cam.cam_bp)
    root.root_bp.register_blueprint(gps.gps_bp)
    root.root_bp.register_blueprint(wifi.wifi_bp)
    app.register_blueprint(root.root_bp)

    # make url_for('index') == url_for('blog.index')
    # in another app, you might define a separate main index here with
    # app.route, while giving the blog blueprint a url_prefix, but for
    # the tutorial the blog will be the main index
    # app.add_url_rule("/", endpoint="index")

    return app


def starts_apps():

    # RESTServer(ARXController.ARXController().create_app()).run()
    # threading.Thread(target=arx.arxRec.run, daemon=True).start()

    # RESTServer(CAMController.CAMController().create_app()).run()
    # threading.Thread(target=cam.camMgr.run, daemon=True).start()

    # RESTServer(GPSController.GPSController().create_app()).run()
    # threading.Thread(target=gps.gpsRet.run, daemon=True).start()

    # RESTServer(WIFIController.WifiController.create_app()).run()
    # threading.Thread(target=wifi.scanner.run, daemon=True).start()

    # wifi_app = WIFIController.WifiController.create_app()
    # wifi_rest = RESTServer(wifi_app)
    # wifi_rest.run()

    # wifi_app = WIFIController.WifiController.create_app()
    # threading.Thread(target=wifi_app.run, daemon=True).start()

    pass


if __name__ == '__main__':


    def stops_apps():
        if wifi.scanner.is_alive():
            wifi.scanner.stop()


    atexit.register(stops_apps)
    configure()
    webapp = return_app_ctx()
    # starts_apps()
    [load_modules(_) for _ in configuration['MODULES']]

    webapp.debug = True
    webapp.run()
