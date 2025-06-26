from flask import Blueprint, render_template, redirect, jsonify

from src.arx.lib.ARXRecorder import ARXRecorder

arxRec = ARXRecorder()
arxRec.configure('arx.json')

arx_bp = Blueprint(
        'arx_bp', __name__, subdomain='arx',
        template_folder=arxRec.config['TEMPLATE_FOLDER'],
        static_folder=arxRec.config['STATIC_FOLDER'],
        static_url_path='/static',
)


@arx_bp.route('/', subdomain='arx')
def index():
    return redirect("/meter", code=302)


@arx_bp.route('/player', methods=['GET'], subdomain='arx')
def arx_player():
    return render_template("arx.html.j2", recorder=arxRec)


@arx_bp.route('/meter', methods=['GET'], subdomain='arx')
def arx_meter():
    return jsonify(arxRec.update_meter())


@arx_bp.route('/mute', methods=['POST'], subdomain='arx')
def arx_mute():
    from src.lib.utils import mute
    return str(mute(arxRec))


