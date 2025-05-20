from flask import Blueprint, redirect, jsonify, render_template

from src.lib.Scanner import Scanner

scanner = Scanner()
scanner.configure('trx.json')

trx_bp = Blueprint(
        'trx_bp', __name__, subdomain='trx',
        template_folder=scanner.config['TEMPLATE_FOLDER'],
        static_folder=scanner.config['STATIC_FOLDER'],
        static_url_path='/static'
)


@trx_bp.route('/', subdomain="trx")
def index():
    return redirect("/scanned", code=302)


@trx_bp.route("/scan", methods=['GET'], subdomain="trx")
def trx_scan():
    """ returns most recent item scanned """
    return jsonify(scanner.module_retriever.scan())


@trx_bp.route("/scanned", methods=['GET'], subdomain="trx")
def trx_scanned():
    return jsonify([worker.get_sgnl() for worker in scanner.module_tracker.workers])

@trx_bp.route("/scanner", methods=['GET'], subdomain="trx")
def trx_scanner():
    return render_template("trx.html.j2", scanner=scanner)


@trx_bp.route("/tracked", methods=['GET'], subdomain="trx")
def trx_tracked():
    return jsonify(scanner.get_tracked_signals())

@trx_bp.route('/add/<uniqId>', methods=['GET', 'POST'], subdomain="trx")
def add(uniqId):
    if scanner.module_retriever.add(uniqId, scanner):
        return "OK", 200
    return "", 404


@trx_bp.route('/mute/<uniqId>', methods=['GET', 'POST'], subdomain="trx")
def mute(uniqId):
    return str(scanner.module_retriever.mute(uniqId, scanner)), 200


@trx_bp.route('/remove/<uniqId>', methods=['GET', 'POST'], subdomain="trx")
def remove(uniqId):
    if scanner.module_retriever.remove(uniqId, scanner):
        return "OK", 200
    return "", 404


@trx_bp.route('/config', methods=['GET'], subdomain='trx')
def trx_config():
    return jsonify(scanner.config)


@trx_bp.route('/stats', methods=['GET'], subdomain='trx')
def trx_stats():
    from src.lib.utils import format_time, format_delta

    stats = {
        'created'       : format_time(scanner.created, "%H:%M:%S"),
        'updated'       : format_time(scanner.updated, "%H:%M:%S"),
        'elapsed'       : format_delta(scanner.elapsed, "%H:%M:%S"),
        'polling_count' : scanner.polling_count,
        'lat'           : scanner.lat,
        'lon'           : scanner.lon,
        # 'workers'     : len(scanner.module_tracker.workers),  implementation based
        'tracked'       : len(scanner.module_tracker.tracked_signals),
        # 'tracked': len(scanner.get_tracked_signals()),
    }
    return jsonify(stats)


@trx_bp.route('/stop', methods=['POST'], subdomain='trx')
def trx_stop():
    # return scanner.retriever.stop()
    return scanner.stop()

@trx_bp.route('/write', methods=['POST'], subdomain='trx')
def trx_write():
    # from lib.wifi_utils import write_to_scanlist
    # if write_to_scanlist(scanner.config, scanner.tracked_signals):
    #     return "OK", 200
    # return "", 500
    pass
