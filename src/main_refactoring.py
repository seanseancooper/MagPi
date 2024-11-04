import os
import importlib
import threading

from flask import Flask
import atexit
import logging.config

import __init__ as root

configuration = {}
logger_root = logging.getLogger('root')

#  ARXController [5001]
#  CAMController [5002]
#       "FORWARD_VIDEO_URL" = "http://10.99.77.1/blackvue_live.cgi"
#       "REVERSE_VIDEO_URL"  = "http://10.99.77.1/blackvue_live.cgi?direction=R"
#       ShowxatingBlackviewPlugin: localhost:6100 (in showxating_plugins.toml) <-- streams symbology & analysis
#  EBSController [5003]
#  GPSController [5004]
#       "GPS_HOST": "192.168.1.2"
#       "MAP_HOST": "localhost:5173"
#       mapping-app (how to move Node.js from default)
#  MOTController [5005]
#  		"MOTION_CPANEL_URL" : "http://192.168.1.4:8080"
#       "MOTION_ALERT_URL" : "http://192.168.1.4:9046"
#  WifiController [5006]
if __name__ == '__main__':

    app = Flask('main', subdomain_matching=True)

    def configure():
        from src.config import readConfig, CONFIG_PATH
        readConfig(os.path.join(CONFIG_PATH, 'controller.json'), configuration)

    def return_app_ctx():

        def load_modules(modconfig):
            m, bp, controller, runmethod, stopmethod = modconfig.split(':')

            # import module m
            m = importlib.import_module(m)

            # BROKEN: start() the app controller.
            # threading.Thread(target=eval(f'm.{controller}.{runmethod}'), daemon=True).start()

            # BROKEN: register this blueprint...
            # root.root_bp.register_blueprint(bp)

        def load_module():

            from ebs import __init__ as ebs
            from arx import __init__ as arx
            from gps import __init__ as gps
            from mot import __init__ as mot
            from wifi import __init__ as wifi
            from cam import __init__ as cam

            from src.lib.rest_server import RESTServer

            # threading.Thread(target=ebs.ebsMgr.ebs_start, daemon=True).start()
            # root.root_bp.register_blueprint(ebs.ebs_bp)

            RESTServer(arx.create_app()).run()
            threading.Thread(target=arx.arxRec.run, daemon=True).start()
            root.root_bp.register_blueprint(arx.arx_bp)

            home = os.getcwd()
            os.chdir(os.path.join(home, 'gps/static/mapping-app/'))
            gps.node.run()
            os.chdir(home)

            RESTServer(gps.create_app()).run()
            threading.Thread(target=gps.gpsRet.run, daemon=True).start()
            root.root_bp.register_blueprint(gps.gps_bp)

            RESTServer(wifi.create_app()).run()
            threading.Thread(target=wifi.scanner.run, daemon=True).start()
            root.root_bp.register_blueprint(wifi.wifi_bp)

            RESTServer(cam.create_app()).run()
            threading.Thread(target=cam.camMgr.run, daemon=True).start()
            root.root_bp.register_blueprint(cam.cam_bp)

        # [load_modules(_) for _ in configuration['MODULES']]
        load_module()

        app.register_blueprint(root.root_bp)
        return app

    def main_stops():
        def unload_module(module):
            application, blueprint, cls, runmethod, stopmethod = module.split(":")
            eval(f"{application}.{cls}.{stopmethod}")

        [unload_module(module) for module in configuration['MODULES']]

    atexit.register(main_stops)


    configure()
    webapp = return_app_ctx()
    webapp.debug = False
    webapp.run()
