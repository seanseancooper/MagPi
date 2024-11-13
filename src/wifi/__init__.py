import os
from flask import Blueprint, redirect, render_template, jsonify

from src.wifi.scanner import WifiScanner
from src.config import CONFIG_PATH

scanner = WifiScanner()
scanner.configure(os.path.join(CONFIG_PATH, 'wifi.json'))

wifi_bp = Blueprint(
        'wifi_bp', __name__, subdomain='wifi',
        template_folder=scanner.config['TEMPLATE_FOLDER'],
        static_folder=scanner.config['STATIC_FOLDER'],
        static_url_path='/static'
)


@wifi_bp.route('/')
def index():
    return redirect("/scan", code=302)


@wifi_bp.route('/add/<bssid>', methods=['POST'], subdomain='wifi')
def wifi_add(bssid):
    if scanner.get_worker(bssid).add(bssid):
        return "OK", 200
    return "", 404


@wifi_bp.route('/tracked', methods=['GET', 'POST'], subdomain='wifi')
def wifi_tracked():
    return jsonify(scanner.get_tracked_signals())


@wifi_bp.route('/ghosts', methods=['GET', 'POST'], subdomain='wifi')
def wifi_ghosts():
    return jsonify(scanner.get_ghost_signals())


@wifi_bp.route('/mute/<bssid>', methods=['POST'], subdomain='wifi')
def wifi_mute(bssid):
    return str(scanner.get_worker(bssid).mute()), 200


@wifi_bp.route('/remove/<bssid>', methods=['POST'], subdomain='wifi')
def wifi_remove(bssid):
    if scanner.get_worker(bssid).remove(bssid):
        return "OK", 200
    return "", 404


@wifi_bp.route('/scan', methods=['GET'], subdomain='wifi')
def wifi_scan():
    return jsonify(scanner.get_parsed_signals())


@wifi_bp.route('/scan/<bssid>', methods=['GET'], subdomain='wifi')
def wifi_scan_bssid(bssid):
    #DBUG this fails to get a worker?!
    worker = scanner.get_worker(bssid)
    if worker.ssid:
        return jsonify(worker.__str__())
    return "", 404


@wifi_bp.route('/scanner', methods=['GET'], subdomain='wifi')
def wifi_scanner():
    """ WIFI scanner UI """
    return render_template("wifi_scan.html.j2", scanner=scanner)


@wifi_bp.route('/stop', methods=['POST'], subdomain='wifi')
def wifi_stop():
    return scanner.stop()


@wifi_bp.route('/write', methods=['POST'], subdomain='wifi')
def wifi_write():
    from lib.wifi_utils import write_to_scanlist
    if write_to_scanlist(scanner.config, scanner.tracked_signals):
        return "OK", 200
    return "", 500


