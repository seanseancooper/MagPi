import os
import importlib
import threading

from flask import Flask
import atexit
import logging.config

import routes as root

configuration = {}
logger_root = logging.getLogger('root')

# Controller [5000]
# >> dependency startup; loading a module loads dependent modules


#  GPSController [5004]
#       "GPS_HOST": "192.168.1.2"
#
# @gps_bp.route('/', subdomain="gps") > redirect("/position", code=302)
# @gps_bp.route("/time", methods=['GET'], subdomain="gps")
# @gps_bp.route("/position", methods=['GET'], subdomain="gps")
# @gps_bp.route("/location", methods=['GET'], subdomain="gps")
# @gps_bp.route("/altitude", methods=['GET'], subdomain="gps")
# @gps_bp.route("/speed", methods=['GET'], subdomain="gps")
# @gps_bp.route("/heading", methods=['GET'], subdomain="gps")
# @gps_bp.route("/climb", methods=['GET'], subdomain="gps")
# @gps_bp.route("/config", methods=['GET'], subdomain="gps")


#  EBSController [5003]
#
# @ebs_bp.route('/')
# @ebs_bp.route('/run', methods=['GET', 'POST'])
# @ebs_bp.route("/stop", methods=['GET', 'POST'])








#  WIFIController [5006]
#
# @wifi_bp.route('/') > redirect("/scan", code=302)
# @wifi_bp.route('/add/<bssid>', methods=['POST'], subdomain='wifi')
# @wifi_bp.route('/tracked', methods=['GET', 'POST'], subdomain='wifi')
# @wifi_bp.route('/ghosts', methods=['GET', 'POST'], subdomain='wifi')
# @wifi_bp.route('/mute/<bssid>', methods=['POST'], subdomain='wifi')
# @wifi_bp.route('/remove/<bssid>', methods=['POST'], subdomain='wifi')
# @wifi_bp.route('/scan', methods=['GET'], subdomain='wifi')
# @wifi_bp.route('/scan/<bssid>', methods=['GET'], subdomain='wifi')
# @wifi_bp.route('/scanner', methods=['GET'], subdomain='wifi')
# @wifi_bp.route('/stop', methods=['POST'], subdomain='wifi')
# @wifi_bp.route('/write', methods=['POST'], subdomain='wifi')


#  TRXController [5009]
#
# @trx_bp.route('/', subdomain="trx") > redirect("/scanned", code=302)
# @trx_bp.route("/scan", methods=['GET'], subdomain="trx")
# @trx_bp.route("/scanned", methods=['GET'], subdomain="trx")


#  SDRController [5008]


#  ARXController [5001]
#
# @arx_bp.route('/', subdomain='arx') > redirect("/player", code=302)
# @arx_bp.route('/player', methods=['GET'], subdomain='arx')
# @arx_bp.route('/meter', methods=['GET'], subdomain='arx')
# @arx_bp.route('/mute', methods=['POST'], subdomain='arx')


#  CAMController [5002]
#       "FORWARD_VIDEO_URL" = "http://10.99.77.1/blackvue_live.cgi"
#       "REVERSE_VIDEO_URL"  = "http://10.99.77.1/blackvue_live.cgi?direction=R"
#  -->  ShowxatingBlackviewPlugin: localhost:6100 (in showxating_plugins.toml) <-- streams symbology & analysis
#
# @cam_bp.route('/') > redirect("/ctrl", code=302)
# @cam_bp.route("/ctrl", methods=['GET'], subdomain='cam')
# @cam_bp.route("/snap", methods=['POST'], subdomain='cam')
# @cam_bp.route("/view/<direction>", methods=['GET', 'POST'], subdomain='cam')
# @cam_bp.route("/multibutton/<mode>", methods=['POST'], subdomain='cam')
# @cam_bp.route("/plugin/<field>/<value>", methods=['POST'], subdomain='cam')
# @cam_bp.route("/move/<command>")










#  MOTController [5010]
#  -->	"MOTION_CAM_URL" : ????
#  		"MOTION_CPANEL_URL" : "http://192.168.1.4:8080"
#       "MOTION_ALERT_URL" : "http://192.168.1.4:9046"
#
# @mot_bp.route('/') > redirect("/controlpanel", code=302)
# @mot_bp.route("/stop", methods=['GET', 'POST'])
# # NOTE: MOT has a control panel of it's own
# @mot_bp.route("/controlpanel", methods=['GET'])







#  MAPController [5005]
#       "MAP":      "localhost:5005"
#       "MAP_HOST": "localhost:5173"
#
# @map_bp.route('/', subdomain='map') > redirect("/aggregated", code=302)
# @map_bp.route("/map", methods=['GET'], subdomain='map')
# @map_bp.route("/aggregated", methods=['GET'], subdomain='map')

#  SCANController [5110]
#       "SCAN":     "localhost:5110"
#

#  NETController [5007]



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

            from ebs import routes as ebs
            from arx import routes as arx
            from gps import routes as gps
            from mot import routes as mot
            from wifi import routes as wifi
            from cam import routes as cam

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
            threading.Thread(target=wifi.s.run, daemon=True).start()
            root.root_bp.register_blueprint(wifi.wifi_bp)

            RESTServer(cam.create_app()).run()
            threading.Thread(target=cam.camMgr.run, name='CAMManager', daemon=True).start()
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
