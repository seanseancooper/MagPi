from flask import Blueprint, redirect, render_template, jsonify
from src.wifi.WifiScanner import WifiScanner
import logging

s = WifiScanner()
s.configure('wifi.json')

wifi_bp = Blueprint(
        'wifi_bp', __name__, subdomain='wifi',
        template_folder=s.config['TEMPLATE_FOLDER'],
        static_folder=s.config['STATIC_FOLDER'],
        static_url_path='/static'
)

speech_logger = logging.getLogger('speech_logger')


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
        return jsonify(worker.get())
    return "", 404


@wifi_bp.route('/scanner', methods=['GET'], subdomain='wifi')
def wifi_scanner():
    """ WIFI scanner UI pre viewcontainer. deprecated. """
    return render_template("wifi.html.j2", scanner=s)


@wifi_bp.route('/tracked', methods=['GET', 'POST'], subdomain='wifi')
def wifi_tracked():
    return jsonify(s.get_tracked_signals())


@wifi_bp.route('/ghosts', methods=['GET', 'POST'], subdomain='wifi')
def wifi_ghosts():
    return jsonify(s.get_ghost_signals())


@wifi_bp.route('/add/<bssid>', methods=['POST'], subdomain='wifi')
def add(bssid):
    if s.get_worker(bssid).add(bssid):
        speech_logger.info(f'added')
        return "OK", 200
    return "", 404


@wifi_bp.route('/mute/<bssid>', methods=['POST'], subdomain='wifi')
def mute(bssid):
    return str(s.get_worker(bssid).mute()), 200


@wifi_bp.route('/remove/<bssid>', methods=['POST'], subdomain='wifi')
def remove(bssid):
    if s.get_worker(bssid).remove(bssid):
        speech_logger.info(f'removed')
        return "OK", 200
    return "", 404


@wifi_bp.route('/config', methods=['GET'], subdomain='wifi')
def wifi_config():
    return jsonify(s.config)


#  TODO: let other apps emit stats as well
@wifi_bp.route('/stats', methods=['GET'], subdomain='wifi')
def wifi_stats():
    from src.lib.utils import format_time, format_delta

    # placeholder; this should already be a map called stats in s. I want to be able to add to that map adhoc.
    stats = {
        'created': format_time(s.created, s.config['TIME_FORMAT']),
        'updated': format_time(s.updated, s.config['TIME_FORMAT']),
        'elapsed': format_delta(s.elapsed, s.config['TIME_FORMAT']),
        'polling_count': s.polling_count,
        'lat': s.lat,
        'lon': s.lon,
        'workers': len(s.workers),
        'tracked': len(s.tracked_signals),
        'ghosts': len(s.ghost_signals),
    }
    return jsonify(stats)


@wifi_bp.route('/stop', methods=['POST'], subdomain='wifi')
def wifi_stop():
    return s.stop()


@wifi_bp.route('/write', methods=['POST'], subdomain='wifi')
def wifi_write():
    from lib.wifi_utils import write_to_scanlist
    if write_to_scanlist(s.config, s.get_tracked_signals()):
        speech_logger.info(f'logged {len(s.get_tracked_signals())} items')
        return "OK", 200
    return "", 500


