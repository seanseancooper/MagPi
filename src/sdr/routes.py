from flask import Blueprint, jsonify, render_template
import logging

import threading
from src.lib.Scanner import Scanner
from src.sdr.lib import SDRAnalyzer

scanner = Scanner()             # run as thread interior to Controller
scanner.configure('sdr.json')

analyzer = SDRAnalyzer()        # sidecar...
analyzer.config = scanner.config

t = threading.Thread(target=scanner.run, daemon=True)
t.start()

sdr_bp = Blueprint(
        'sdr_bp', __name__, subdomain='sdr',
        template_folder=scanner.config['TEMPLATE_FOLDER'],
        static_folder=scanner.config['STATIC_FOLDER'],
        static_url_path='/static'
)

speech_logger = logging.getLogger('speech_logger')


@sdr_bp.route('/', methods=['GET'], subdomain='sdr')
def index():
    return render_template('sdr.html.j2', analyzer=analyzer)


@sdr_bp.route('/scan', methods=['GET'], subdomain='sdr')
def sdr_scan():
    return jsonify(scanner.get_parsed_signals())

@sdr_bp.route('/scan/<ident>', methods=['GET'], subdomain='sdr')
def sdr_scan_ident(ident):
    worker = scanner.module_tracker.get_worker(ident)
    if worker:
        return jsonify(worker.get())
    return "", 404

@sdr_bp.route('/tracked', methods=['GET', 'POST'], subdomain='sdr')
def sdr_tracked():
    return jsonify(scanner.get_tracked_signals())


@sdr_bp.route('/ghosts', methods=['GET', 'POST'], subdomain='sdr')
def sdr_ghosts():
    return jsonify(scanner.get_ghost_signals())


@sdr_bp.route('/add/<ident>', methods=['POST'], subdomain='sdr')
def add(ident):
    if scanner.module_tracker.get_worker(ident).add(ident):
        if scanner.config['SPEECH_ENABLED']:
            speech_logger.info(f'added')
        return "OK", 200
    return "", 404


@sdr_bp.route('/mute/<ident>', methods=['POST'], subdomain='sdr')
def mute(ident):
    return str(scanner.module_tracker.get_worker(ident).mute()), 200


@sdr_bp.route('/remove/<ident>', methods=['POST'], subdomain='sdr')
def remove(ident):
    if scanner.module_tracker.get_worker(ident).remove(ident):
        if scanner.config['SPEECH_ENABLED']:
            speech_logger.info(f'removed')
        return "OK", 200
    return "", 404


@sdr_bp.route('/config', methods=['GET'], subdomain='sdr')
def sdr_config():
    return jsonify(scanner.config)


#  TODO: let other apps emit stats as well
@sdr_bp.route('/stats', methods=['GET'], subdomain='sdr')
def sdr_stats():
    return jsonify(scanner.stats)


@sdr_bp.route('/stop', methods=['POST'], subdomain='sdr')
def sdr_stop():
    return scanner.stop()




