import os
import threading
import time
from datetime import datetime, timedelta

import flask
from flask import g, Blueprint, redirect, request, render_template, current_app
import requests

from src.config import CONFIG_PATH, readConfig


class Scanner(threading.Thread):  # rename me; I'm not a scanner...

    def __init__(self):
        super().__init__()

        self.polling_count = 0
        self.workers = []
        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()
        self.config = {}

    def stop(self):
        print(f'stopping.')
        pass

    def configure(self, config_file):
        readConfig(config_file, self.config)

    def run(self):
        while True:
            self.updated = datetime.now()
            self.elapsed = datetime.now() - self.created
            time.sleep(1)
            pass


def get_scanner():
    with current_app.app_context():
        if "scanner" not in g:
            g.scanner = Scanner()
        return g.scanner


scanner = Scanner()
# scanner = get_scanner()
scanner.configure(os.path.join(CONFIG_PATH, 'scan.json'))
scan_bp = Blueprint(
        'scan_bp', __name__, subdomain='scan',
        template_folder=scanner.config['TEMPLATE_FOLDER'],
        static_folder=scanner.config['STATIC_FOLDER']
)


@scan_bp.route('/')
def index():
    return redirect("/scanner", code=302)


@scan_bp.route('/scanner', methods=['GET'], subdomain='scan')
def scan_scanner():
    """ scan scanner UI """
    return render_template("scanner.html.j2", scanner=scanner, blueprint=scan_bp)


@scan_bp.route('/add/<id>', methods=['POST'], subdomain='scan')
def add(id):

    MOD = request.headers['TARGET']
    resp = requests.get('http://map.localhost:5005/config/' + MOD)
    config = resp.json()

    return redirect(f'http://{MOD}.{config["SERVER_NAME"]}/add/{id}', 307)


@scan_bp.route('/mute/<id>', methods=['POST'], subdomain='scan')
def mute(id):

    MOD = request.headers['TARGET']
    resp = requests.get('http://map.localhost:5005/config/' + MOD)
    config  = resp.json()

    return redirect(f'http://{MOD}.{config["SERVER_NAME"]}/mute/{id}', 307)


@scan_bp.route('/remove/<id>', methods=['POST'], subdomain='scan')
def remove(id):

    MOD = request.headers['TARGET']
    resp = requests.get('http://map.localhost:5005/config/' + MOD)
    config  = resp.json()

    return redirect(f'http://{MOD}.{config["SERVER_NAME"]}/remove/{id}', 307)


@scan_bp.route('/write', methods=['POST'], subdomain='scan')
def write():

    MOD = request.headers['TARGET']
    resp = requests.get('http://map.localhost:5005/config/' + MOD)
    config  = resp.json()

    return redirect(f'http://{MOD}.{config["SERVER_NAME"]}/write', 307)


@scan_bp.route('/stop', methods=['POST'], subdomain='scan')
def stop():
    return "OK", 200


