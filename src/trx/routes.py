from flask import Blueprint, redirect, jsonify
from src.trx.TRXProducer import TRXMQProducer

trxProd = TRXMQProducer()
trxProd.configure('trx.json')

trx_bp = Blueprint(
        'trx_bp', __name__, subdomain='trx',
        template_folder=trxProd.config['TEMPLATE_FOLDER'],
        static_folder=trxProd.config['STATIC_FOLDER'],
        static_url_path='/static'
)


@trx_bp.route('/', subdomain="trx")
def index():
    return redirect("/scanned", code=302)


@trx_bp.route("/scan", methods=['GET'], subdomain="trx")
def trx_scan():
    """ returns most recent item scanned """
    return jsonify(trxProd.retriever.scan())


@trx_bp.route("/scanned", methods=['GET'], subdomain="trx")
def trx_scanned():
    return jsonify(trxProd.retriever.get_scanned())


@trx_bp.route("/tracked", methods=['GET'], subdomain="trx")
def trx_tracked():
    return jsonify(trxProd.retriever.get_tracked())


@trx_bp.route('/add/<id>', methods=['GET', 'POST'], subdomain="trx")
def add(id):
    if trxProd.retriever.add(id):
        return "OK", 200
    return "", 404


@trx_bp.route('/mute/<id>', methods=['GET', 'POST'], subdomain="trx")
def mute(id):
    return str(trxProd.retriever.mute(id)), 200


@trx_bp.route('/remove/<id>', methods=['GET', 'POST'], subdomain="trx")
def remove(id):
    if trxProd.retriever.remove(id):
        return "OK", 200
    return "", 404


@trx_bp.route('/config', methods=['GET'], subdomain='trx')
def trx_config():
    return jsonify(trxProd.config)


@trx_bp.route('/stats', methods=['GET'], subdomain='trx')
def trx_stats():
    from src.lib.utils import format_time, format_delta

    stats = {
        'created'       : format_time(trxProd.created, "%H:%M:%S"),
        'updated'       : format_time(trxProd.updated, "%H:%M:%S"),
        'elapsed'       : format_delta(trxProd.elapsed, "%H:%M:%S"),
        'polling_count' : trxProd.polling_count,
        'lat'           : trxProd.lat,
        'lon'           : trxProd.lon,
        # 'workers'     : len(trxRet.workers),  implementation based
        'tracked'       : len(trxProd.tracked_signals),
    }
    return jsonify(stats)


@trx_bp.route('/stop', methods=['POST'], subdomain='wifi')
def trx_stop():
    return trxProd.retriever.stop()


@trx_bp.route('/write', methods=['POST'], subdomain='wifi')
def trx_write():
    # from lib.wifi_utils import write_to_scanlist
    # if write_to_scanlist(scanner.config, scanner.tracked_signals):
    #     return "OK", 200
    # return "", 500
    pass
