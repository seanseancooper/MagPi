import os
import threading
import time
from datetime import timedelta

import flask
from flask import Blueprint, redirect, render_template

from src.config import CONFIG_PATH, readConfig


class Scanner(threading.Thread):

    def __init__(self):
        super().__init__()

        self.polling_count = 0
        self.workers = []
        self.elapsed = timedelta()
        self.config = {}

    def stop(self):
        print(f'stopping.')
        pass

    def configure(self, config_file):
        readConfig(config_file, self.config)

    def run(self):
        while True:
            time.sleep(1)
            pass


scanner = Scanner()
scanner.configure(os.path.join(CONFIG_PATH, 'scan.json'))

app = flask.current_app

scan_bp = Blueprint(
        'scan_bp', __name__, subdomain='scan',
        template_folder=scanner.config['TEMPLATE_FOLDER'],
        static_folder=scanner.config['STATIC_FOLDER']
)


@scan_bp.route('/')
def index():
    return redirect("/scanner", code=302)


@scan_bp.route('/scanner', methods=['GET'], subdomain='scan')
def scan_scanner():
    """ scan scanner UI """
    return render_template("scanner.html.j2", scanner=scanner, blueprint=scan_bp)


@scan_bp.route('/add/<id>', methods=['POST'], subdomain='scan')
def add(id):

    MOD = 'WIFI'
    # forward request to the correct module/app/bp
    # examine the header/request?
    # from flask import request
    # MOD = request.headers.environ['MODULE_TARGET']

    # or match the the form of the id?
    # 3A:FF:45:AC:DD:0E IS A BSSID
    # 201326592 IS A FREQUENCY

    # get config from the MAPAggregator?
    # resp = requests.get('http://map.localhost:5005/aggregated/'+ MOD + '/config'"
    # config  = json.parse(resp)
    # SERVER_NAME  = config['SERVER_NAME']

    SERVER_NAME = 'localhost:5006'

    CONTEXT = 'add'  # this methodname, the request URI...

    forward = f'http://{MOD}.{SERVER_NAME}/{CONTEXT}/{id}'
    code = 307

    # redirect as 307 to temp context
    # redirect as 308 to correct context
    return redirect(forward, code=code)


@scan_bp.route('/mute/<id>', methods=['POST'], subdomain='scan')
def mute(id):

    MOD = 'WIFI'
    SERVER_NAME = 'localhost:5006'
    CONTEXT = 'mute'  # this methodname, the request URI...
    forward = f'http://{MOD}.{SERVER_NAME}/{CONTEXT}/{id}'
    code = 307

    return redirect(forward, code=code)


@scan_bp.route('/remove/<id>', methods=['POST'], subdomain='scan')
def remove(id):

    MOD = 'WIFI'
    SERVER_NAME = 'localhost:5006'
    CONTEXT = 'remove'  # this methodname, the request URI...
    forward = f'http://{MOD}.{SERVER_NAME}/{CONTEXT}/{id}'
    code = 307

    return redirect(forward, code=code)


@scan_bp.route('/write', methods=['POST'], subdomain='scan')
def write():
    from src.wifi.lib.wifi_utils import write_to_scanlist
    tracked_signals = None
    if write_to_scanlist(scanner.config, tracked_signals):
        return "OK", 200
    return "", 500


@scan_bp.route('/stop', methods=['POST'], subdomain='scan')
def stop():
    return "OK", 200


