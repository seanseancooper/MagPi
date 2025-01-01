from flask import Blueprint, redirect, request, render_template
import requests

from src.view.ViewContainer import ViewContainer


viewContainer = ViewContainer()
# TODO: the config hasn't been read yet, how can these be configurable?
non_config_files = ['arx.json', 'ebs.json', 'mot.json']
viewContainer.configure('view.json', non_config_files=non_config_files)

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


@vc_bp.route(f'/<path>', methods=['POST'], subdomain='view')
def reroute_to_module(path):

    MOD = request.headers['TARGET']
    resp = requests.get('http://view.localhost:5110/config/' + MOD)
    config = resp.json()

    return redirect(f'http://{MOD}.{config["SERVER_NAME"]}{request.path}', 307)


# OPS BUTTONS
@vc_bp.route('/add/<id>', methods=['POST'], subdomain='view')
def add(id):

    MOD = request.headers['TARGET']
    resp = requests.get('http://view.localhost:5110/config/' + MOD)
    config = resp.json()

    return redirect(f'http://{MOD}.{config["SERVER_NAME"]}/add/{id}', 307)


@vc_bp.route('/mute/<id>', methods=['POST'], subdomain='view')
def mute(id):

    MOD = request.headers['TARGET']
    resp = requests.get('http://view.localhost:5110/config/' + MOD)
    config = resp.json()

    return redirect(f'http://{MOD}.{config["SERVER_NAME"]}/mute/{id}', 307)


@vc_bp.route('/remove/<id>', methods=['POST'], subdomain='view')
def remove(id):

    MOD = request.headers['TARGET']
    resp = requests.get('http://view.localhost:5110/config/' + MOD)
    config = resp.json()

    return redirect(f'http://{MOD}.{config["SERVER_NAME"]}/remove/{id}', 307)


@vc_bp.route('/write', methods=['POST'], subdomain='view')
def write():

    MOD = request.headers['TARGET']
    resp = requests.get('http://view.localhost:5110/config/' + MOD)
    config = resp.json()

    return redirect(f'http://{MOD}.{config["SERVER_NAME"]}/write', 307)



# AGGREGATOR CONTEXTS
@vc_bp.route("/config/<mod>", methods=['GET'], subdomain='view')
def config_for_module(mod):
    """ returns module specific config"""
    return viewContainer.module_configs[mod]


@vc_bp.route("/stats", methods=['GET'], subdomain='view')
def module_stats():
    """ returns module stats"""
    return viewContainer.module_stats


@vc_bp.route("/stats/<mod>", methods=['GET'], subdomain='view')
def stats_for_module(mod):
    """ returns module specific stats"""
    return viewContainer.module_stats[mod]


@vc_bp.route("/aggregated", methods=['GET'], subdomain='view')
def aggregated():
    """  returns all aggregated data """
    return viewContainer.module_aggregated
    # TODO: move to manager
    # _configs = viewContainer.module_configs
    # _configs['stats'] = viewContainer.module_stats
    # return jsonify(_configs)


@vc_bp.route("/aggregated/<mod>", methods=['GET'], subdomain='view')
def aggregated_by_module(mod):
    """ returns module specific aggregated data"""
    return viewContainer.module_aggregated[mod]
    # _configs = viewContainer.module_configs[mod]
    # _configs['stats'] = viewContainer.module_stats[mod]
    # return jsonify(_configs)


@vc_bp.route("/aggregated/<mod>/<context>", methods=['GET'], subdomain='view')
def aggregated_by_module_context(mod, context):
    """ redirect to a specific context of a module """
    return redirect('http://' + mod + '.' + viewContainer.module_configs[mod]['SERVER_NAME'] + '/' + context, code=302)


# CONTROL
@vc_bp.route('/reload/<mod>', subdomain='view')
def reload(mod):
    if viewContainer.reload(mod):
        return "OK", 200
    return "FAIL", 500


@vc_bp.route('/unload/<mod>', subdomain='view')
def unload(mod):
    if viewContainer.unload(mod):
        return "OK", 200
    return "FAIL", 500


@vc_bp.route('/stop', methods=['POST'], subdomain='view')
def stop():
    return "OK", 200
