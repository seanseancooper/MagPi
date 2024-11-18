import os
from flask import Blueprint, redirect

from src.trx.TRXSerialRetriever import TRXSerialRetriever
from src.trx.TRXUSBRetriever import TRXUSBRetriever
from src.config import CONFIG_PATH

trxRet = TRXUSBRetriever()
trxRet.configure(os.path.join(CONFIG_PATH, 'trx.json'))

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
    return trxRet.get_scan()


@trx_bp.route("/scanned", methods=['GET'], subdomain="trx")
def trx_scanned():
    return trxRet.get_scanned()


@trx_bp.route("/tracked", methods=['GET'], subdomain="trx")
def get_tracked():
    return trxRet.get_tracked()


@trx_bp.route('/mute/<sgnl>', methods=['GET', 'POST'], subdomain="trx")
def trx_mute(sgnl):
    if trxRet.mute(sgnl):
        return "OK", 200
    return "", 404


@trx_bp.route('/add/<freq>', methods=['GET', 'POST'], subdomain="trx")
def trx_add(freq):
    if trxRet.add(freq):
        return "OK", 200
    return "", 404


@trx_bp.route('/remove/<freq>', methods=['GET', 'POST'], subdomain="trx")
def trx_remove(freq):
    if trxRet.remove(freq):
        return "OK", 200
    return "", 404

