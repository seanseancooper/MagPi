from flask import Blueprint, redirect, render_template, jsonify
import logging

from src.lib.Scanner import Scanner

scanner = Scanner()
scanner.configure('wifi.json')

wifi_bp = Blueprint(
        'wifi_bp', __name__, subdomain='wifi',
        template_folder=scanner.config['TEMPLATE_FOLDER'],
        static_folder=scanner.config['STATIC_FOLDER'],
        static_url_path='/static'
)

speech_logger = logging.getLogger('speech_logger')


@wifi_bp.route('/', subdomain="wifi")
def index():
    return redirect("/scan", code=302)


@wifi_bp.route('/scan', methods=['GET'], subdomain='wifi')
def wifi_scan():
    return jsonify(scanner.get_parsed_signals())


@wifi_bp.route('/scan/<bssid>', methods=['GET'], subdomain='wifi')
def wifi_scan_bssid(bssid):
    worker = scanner.module_tracker.get_worker(bssid)
    if worker:
        return jsonify(worker.get())
    return "", 404


@wifi_bp.route('/scanner', methods=['GET'], subdomain='wifi')
def wifi_scanner():
    """ WIFI scanner UI pre viewcontainer. deprecated. """
    return render_template("wifi.html.j2", scanner=scanner)


@wifi_bp.route('/tracked', methods=['GET', 'POST'], subdomain='wifi')
def wifi_tracked():
    return jsonify(scanner.get_tracked_signals())


@wifi_bp.route('/ghosts', methods=['GET', 'POST'], subdomain='wifi')
def wifi_ghosts():
    return jsonify(scanner.get_ghost_signals())


@wifi_bp.route('/workers', methods=['GET', 'POST'], subdomain='wifi')
def wifi_workers():
    return jsonify(scanner.get_workers())


@wifi_bp.route('/add/<bssid>', methods=['POST'], subdomain='wifi')
def add(bssid):
    if scanner.module_tracker.get_worker(bssid).add(bssid):
        if scanner.config['SPEECH_ENABLED']:
            speech_logger.info(f'added')
        return "OK", 200
    return "", 404


@wifi_bp.route('/mute/<bssid>', methods=['POST'], subdomain='wifi')
def mute(bssid):
    return str(scanner.module_tracker.get_worker(bssid).mute()), 200


@wifi_bp.route('/remove/<bssid>', methods=['POST'], subdomain='wifi')
def remove(bssid):
    if scanner.module_tracker.get_worker(bssid).remove(bssid):
        if scanner.config['SPEECH_ENABLED']:
            speech_logger.info(f'removed')
        return "OK", 200
    return "", 404


@wifi_bp.route('/config', methods=['GET'], subdomain='wifi')
def wifi_config():
    return jsonify(scanner.config)


#  TODO: let other apps emit stats as well
@wifi_bp.route('/stats', methods=['GET'], subdomain='wifi')
def wifi_stats():
    return jsonify(scanner.stats)


@wifi_bp.route('/stop', methods=['POST'], subdomain='wifi')
def wifi_stop():
    return scanner.stop()


@wifi_bp.route('/write', methods=['POST'], subdomain='wifi')
def wifi_write():
    from src.wifi.lib.wifi_utils import write_to_scanlist
    if write_to_scanlist(scanner.config, scanner.get_tracked_signals()):
        if scanner.config['SPEECH_ENABLED']:
            speech_logger.info(f'logged {len(scanner.get_tracked_signals())} items')
        return "OK", 200
    return "", 404


