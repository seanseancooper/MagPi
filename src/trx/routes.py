import os
from flask import Blueprint, redirect

from src.trx.TRXSerialRetriever import TRXSerialRetriever
from src.config import CONFIG_PATH

trxRet = TRXSerialRetriever()
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


