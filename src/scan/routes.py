import os
import threading
import time
from datetime import timedelta

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

scan_bp = Blueprint(
        'scan_bp', __name__, subdomain='scan',
        template_folder=scanner.config['TEMPLATE_FOLDER'],
        static_folder=scanner.config['STATIC_FOLDER'],
        static_url_path='/static'
)


@scan_bp.route('/')
def index():
    return redirect("/scanner", code=302)


@scan_bp.route('/scanner', methods=['GET'], subdomain='scan')
def scan_scanner():
    """ scan scanner UI """
    return render_template("scanner.html.j2", scanner=scanner)


@scan_bp.route('/scanner', methods=['GET'], subdomain='scan')
def scan_tracked():
    """ scan scanner UI """
    return redirect("/scanner", code=302)


@scan_bp.route('/scanner', methods=['GET'], subdomain='scan')
def scan_ghosts():
    """ scan scanner UI """
    return redirect("/scanner", code=302)


@scan_bp.route('/add/<bssid>', methods=['POST'], subdomain='scan')
def scan_add(bssid):
    # add by type;
    return "OK", 200


@scan_bp.route('/mute/<bssid>', methods=['POST'], subdomain='scan')
def scan_mute(bssid):
    return "OK", 200


@scan_bp.route('/remove/<bssid>', methods=['POST'], subdomain='scan')
def scan_remove(bssid):
    return "OK", 200


@scan_bp.route('/write', methods=['POST'], subdomain='scan')
def scan_write():
    from src.wifi.lib.wifi_utils import write_to_scanlist
    tracked_signals = None
    if write_to_scanlist(scanner.config, tracked_signals):
        return "OK", 200
    return "", 500


