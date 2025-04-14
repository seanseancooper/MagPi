from flask import Blueprint, redirect, jsonify
from src.net.rabbitMQ.RabbitMQTRXProducer import RabbitMQTRXProducer

trxRet = RabbitMQTRXProducer()
trxRet.configure('trx.json')

trx_bp = Blueprint(
        'trx_bp', __name__, subdomain='trx',
        template_folder=trxRet.config['TEMPLATE_FOLDER'],
        static_folder=trxRet.config['STATIC_FOLDER'],
        static_url_path='/static'
)


@trx_bp.route('/', subdomain="trx")
def index():
    return redirect("/scanned", code=302)


@trx_bp.route("/scan", methods=['GET'], subdomain="trx")
def trx_scan():
    """ returns most recent item scanned """
    return jsonify(trxRet.scan())


@trx_bp.route("/scanned", methods=['GET'], subdomain="trx")
def trx_scanned():
    return jsonify(trxRet.get_scanned())


@trx_bp.route("/tracked", methods=['GET'], subdomain="trx")
def trx_tracked():
    return jsonify(trxRet.get_tracked())


@trx_bp.route('/add/<id>', methods=['GET', 'POST'], subdomain="trx")
def add(id):
    if trxRet.add(id):
        return "OK", 200
    return "", 404


@trx_bp.route('/mute/<id>', methods=['GET', 'POST'], subdomain="trx")
def mute(id):
    return str(trxRet.mute(id)), 200


@trx_bp.route('/remove/<id>', methods=['GET', 'POST'], subdomain="trx")
def remove(id):
    if trxRet.remove(id):
        return "OK", 200
    return "", 404


@trx_bp.route('/config', methods=['GET'], subdomain='trx')
def trx_config():
    return jsonify(trxRet.config)


@trx_bp.route('/stats', methods=['GET'], subdomain='trx')
def trx_stats():
    from src.lib.utils import format_time, format_delta

    stats = {
        'created'       : format_time(trxRet.created, "%H:%M:%S"),
        'updated'       : format_time(trxRet.updated, "%H:%M:%S"),
        'elapsed'       : format_delta(trxRet.elapsed, "%H:%M:%S"),
        'polling_count' : trxRet.polling_count,
        'lat'           : trxRet.lat,
        'lon'           : trxRet.lon,
        # 'workers'     : len(trxRet.workers),  implementation based
        'tracked'       : len(trxRet.tracked_signals),
    }
    return jsonify(stats)


@trx_bp.route('/stop', methods=['POST'], subdomain='wifi')
def trx_stop():
    return trxRet.stop()


@trx_bp.route('/write', methods=['POST'], subdomain='wifi')
def trx_write():
    # from lib.wifi_utils import write_to_scanlist
    # if write_to_scanlist(scanner.config, scanner.tracked_signals):
    #     return "OK", 200
    # return "", 500
    pass
