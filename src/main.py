import os
import threading
import importlib
from flask import Flask
from flask import g
import atexit


from src.lib.rest_server import RESTServer

import src.arx.ARXController as ARXController
import src.cam.CAMController as CAMController
import src.gps.GPSController as GPSController
import src.map.MAPController as MAPController
import src.trx.TRXController as TRXController
import src.scan.ViewController as SCANController


from arx import routes as arx
from cam import routes as cam
from gps import routes as gps
from map import routes as map
from trx import routes as trx
from wifi import routes as wifi  # can't get retriever! not in path
from scan import routes as scan

import routes as root
configuration = {}


def configure():
    from src.config import readConfig, CONFIG_PATH
    readConfig(os.path.join(CONFIG_PATH, 'controller.json'), configuration)


# def load_modules(modconfig):
#     m, bp, controller, runmethod, stopmethod = modconfig.split(':')
#
#     # import module m
#     mdle = importlib.import_module(m)
#
#     # BROKEN: start() the app controller.
#     threading.Thread(target=mdle.WIFIController.WifiController.run, daemon=True).start()


def create_app():

    app = Flask(__name__, instance_relative_config=True)
    app.config['SERVER_NAME'] = configuration['SERVER_NAME']

    root.root_bp.register_blueprint(gps.gps_bp)
    root.root_bp.register_blueprint(wifi.wifi_bp)

    root.root_bp.register_blueprint(trx.trx_bp)
    root.root_bp.register_blueprint(arx.arx_bp)
    root.root_bp.register_blueprint(cam.cam_bp)

    root.root_bp.register_blueprint(map.map_bp)

    scan.viewContainer = scan.get_scanner(app)
    root.root_bp.register_blueprint(scan.vc_bp)

    app.register_blueprint(root.root_bp)

    # make url_for('index') == url_for('blog.index')
    # in another app, you might define a separate main index here with
    # app.route, while giving the blog blueprint a url_prefix, but for
    # the tutorial the blog will be the main index
    # app.add_url_rule("/", endpoint="index")

    return app


def starts_apps():
    # Controller [5000]
    # >> dependency startup; loading a module loads dependent modules
        #  SCANController [5110]
            #  MAPController [5005]
                #  GPSController [5004]
                    #  WIFIController [5006]
                    #  TRXController [5009]
                    #  SDRController [5008]
                    #  ARXController [5001]
                        #  CAMController [5002]
                #  NETController [5007]
            #  MOTController [5010]
            #  EBSController [5003]

    RESTServer(GPSController.GPSController().create_app()).run()
    threading.Thread(target=gps.gpsRet.run, daemon=True).start()

    import wifi.__init__ as wifirunner
    RESTServer(wifirunner.w.create_app()).run()
    wifirunner.w.run()

    RESTServer(TRXController.TRXController.create_app()).run()
    threading.Thread(target=trx.trxRet.run, daemon=True).start()

    RESTServer(ARXController.ARXController().create_app()).run()
    threading.Thread(target=arx.arxRec.run, daemon=True).start()

    RESTServer(CAMController.CAMController().create_app()).run()
    threading.Thread(target=cam.camMgr.run, daemon=True).start()

    RESTServer(MAPController.MAPController.create_app()).run()
    threading.Thread(target=map.mapAgg.run, daemon=True).start()

    RESTServer(SCANController.ViewController.create_app()).run()
    threading.Thread(target=scan.viewContainer.run, daemon=True).start()


if __name__ == '__main__':


    configure()
    webapp = create_app()
    starts_apps()
    # [load_modules(_) for _ in configuration['MODULES']]

    webapp.debug = True
    webapp.run()
