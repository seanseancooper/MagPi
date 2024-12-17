from flask import Blueprint, redirect, request, render_template
import requests

from src.view.ViewContainer import ViewContainer


viewContainer = ViewContainer()

viewContainer.configure('view.json')
vc_bp = Blueprint(
        'vc_bp', __name__, subdomain='view',
        template_folder=viewContainer.config['TEMPLATE_FOLDER'],
        static_folder=viewContainer.config['STATIC_FOLDER']
)


@vc_bp.route('/')
def index():
    return redirect("/view", code=302)


@vc_bp.route('/view', methods=['GET'], subdomain='view')
def vc_view():
    """ ViewController UI """
    return render_template("view_container.html.j2", container=viewContainer, blueprint=vc_bp)


@vc_bp.route('/add/<id>', methods=['POST'], subdomain='view')
def add(id):

    MOD = request.headers['TARGET']
    resp = requests.get('http://map.localhost:5005/config/' + MOD)
    config = resp.json()

    return redirect(f'http://{MOD}.{config["SERVER_NAME"]}/add/{id}', 307)


@vc_bp.route('/mute/<id>', methods=['POST'], subdomain='view')
def mute(id):

    MOD = request.headers['TARGET']
    resp = requests.get('http://map.localhost:5005/config/' + MOD)
    config = resp.json()

    return redirect(f'http://{MOD}.{config["SERVER_NAME"]}/mute/{id}', 307)


@vc_bp.route('/remove/<id>', methods=['POST'], subdomain='view')
def remove(id):

    MOD = request.headers['TARGET']
    resp = requests.get('http://map.localhost:5005/config/' + MOD)
    config = resp.json()

    return redirect(f'http://{MOD}.{config["SERVER_NAME"]}/remove/{id}', 307)


@vc_bp.route('/write', methods=['POST'], subdomain='view')
def write():

    MOD = request.headers['TARGET']
    resp = requests.get('http://map.localhost:5005/config/' + MOD)
    config = resp.json()

    return redirect(f'http://{MOD}.{config["SERVER_NAME"]}/write', 307)


# IdeA: can routes be unified?
#  perhaps this can the basis for supporting a module specific button fragment?

@vc_bp.route(f'/<path>', methods=['POST'], subdomain='view')
def reroute_to_module(path):

    MOD = request.headers['TARGET']
    resp = requests.get('http://map.localhost:5005/config/' + MOD)
    config = resp.json()

    return redirect(f'http://{MOD}.{config["SERVER_NAME"]}{request.path}', 307)


@vc_bp.route('/stop', methods=['POST'], subdomain='view')
def stop():
    return "OK", 200


