import os
from flask import Blueprint, redirect, render_template

from src.trx.TRXRetriever import TRXRetriever
from src.config import CONFIG_PATH

trxRet = TRXRetriever()
trxRet.configure(os.path.join(CONFIG_PATH, 'trx.json'))

trx_bp = Blueprint(
        'trx_bp', __name__, subdomain='trx',
        template_folder=trxRet.config['TEMPLATE_FOLDER'],
        static_folder=trxRet.config['STATIC_FOLDER'],
        static_url_path='/static'
)


@trx_bp.route('/', subdomain="trx")
def index():
    return redirect("/scan", code=302)


@trx_bp.route("/scan", methods=['GET'], subdomain="trx")
def trx_scan():
    import json
    return trxRet.run()


