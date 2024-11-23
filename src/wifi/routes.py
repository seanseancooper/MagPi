import os
from flask import Blueprint, redirect, render_template, jsonify

from src.wifi.WifiScanner import WifiScanner
from src.config import CONFIG_PATH

s = WifiScanner()
s.configure(os.path.join(CONFIG_PATH, 'wifi.json'))

wifi_bp = Blueprint(
        'wifi_bp', __name__, subdomain='wifi',
        template_folder=s.config['TEMPLATE_FOLDER'],
        static_folder=s.config['STATIC_FOLDER'],
        static_url_path='/static'
)


@wifi_bp.route('/', subdomain="wifi")
def index():
    return redirect("/scan", code=302)


@wifi_bp.route('/scan', methods=['GET'], subdomain='wifi')
def wifi_scan():
    return jsonify(s.get_parsed_signals())


@wifi_bp.route('/scan/<bssid>', methods=['GET'], subdomain='wifi')
def wifi_scan_bssid(bssid):
    worker = s.get_worker(bssid)
    if worker:
        return jsonify(worker.__str__())
    return "", 404


@wifi_bp.route('/scanner', methods=['GET'], subdomain='wifi')
def wifi_scanner():
    """ WIFI scanner UI """
    return render_template("wifi_scan.html.j2", scanner=s)


@wifi_bp.route('/tracked', methods=['GET', 'POST'], subdomain='wifi')
def wifi_tracked():
    return jsonify(s.get_tracked_signals())


@wifi_bp.route('/ghosts', methods=['GET', 'POST'], subdomain='wifi')
def wifi_ghosts():
    return jsonify(s.get_ghost_signals())


@wifi_bp.route('/add/<bssid>', methods=['POST'], subdomain='wifi')
def add(bssid):
    if s.get_worker(bssid).add(bssid):
        return "OK", 200
    return "", 404


@wifi_bp.route('/mute/<bssid>', methods=['POST'], subdomain='wifi')
def mute(bssid):
    return str(s.get_worker(bssid).mute()), 200


@wifi_bp.route('/remove/<bssid>', methods=['POST'], subdomain='wifi')
def remove(bssid):
    if s.get_worker(bssid).remove(bssid):
        return "OK", 200
    return "", 404


@wifi_bp.route('/config', methods=['GET'], subdomain='wifi')
def wifi_config():
    return jsonify(s.config)


@wifi_bp.route('/stop', methods=['POST'], subdomain='wifi')
def wifi_stop():
    return s.stop()


@wifi_bp.route('/write', methods=['POST'], subdomain='wifi')
def wifi_write():
    from lib.wifi_utils import write_to_scanlist
    if write_to_scanlist(s.config, s.tracked_signals):
        return "OK", 200
    return "", 500


