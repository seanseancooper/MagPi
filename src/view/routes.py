import os

from flask import Blueprint, redirect, request, render_template
import requests

from src.config import CONFIG_PATH
from ViewContainer import ViewContainer


viewContainer = ViewContainer()

viewContainer.configure(os.path.join(CONFIG_PATH, 'view.json'))
vc_bp = Blueprint(
        'vc_bp', __name__, subdomain='scan',
        template_folder=viewContainer.config['TEMPLATE_FOLDER'],
        static_folder=viewContainer.config['STATIC_FOLDER']
)


@vc_bp.route('/')
def index():
    return redirect("/scanner", code=302)


@vc_bp.route('/scanner', methods=['GET'], subdomain='scan')
def scan_scanner():
    """ scan scanner UI """
    return render_template("scanner.html.j2", container=viewContainer, blueprint=vc_bp)


@vc_bp.route('/add/<id>', methods=['POST'], subdomain='scan')
def add(id):

    MOD = request.headers['TARGET']
    resp = requests.get('http://map.localhost:5005/config/' + MOD)
    config = resp.json()

    return redirect(f'http://{MOD}.{config["SERVER_NAME"]}/add/{id}', 307)


@vc_bp.route('/mute/<id>', methods=['POST'], subdomain='scan')
def mute(id):

    MOD = request.headers['TARGET']
    resp = requests.get('http://map.localhost:5005/config/' + MOD)
    config  = resp.json()

    return redirect(f'http://{MOD}.{config["SERVER_NAME"]}/mute/{id}', 307)


@vc_bp.route('/remove/<id>', methods=['POST'], subdomain='scan')
def remove(id):

    MOD = request.headers['TARGET']
    resp = requests.get('http://map.localhost:5005/config/' + MOD)
    config  = resp.json()

    return redirect(f'http://{MOD}.{config["SERVER_NAME"]}/remove/{id}', 307)


@vc_bp.route('/write', methods=['POST'], subdomain='scan')
def write():

    MOD = request.headers['TARGET']
    resp = requests.get('http://map.localhost:5005/config/' + MOD)
    config  = resp.json()

    return redirect(f'http://{MOD}.{config["SERVER_NAME"]}/write', 307)


@vc_bp.route('/stop', methods=['POST'], subdomain='scan')
def stop():
    return "OK", 200


