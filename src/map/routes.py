from flask import Blueprint, redirect, render_template

from src.map.MAPAggregator import MAPAggregator

mapAgg = MAPAggregator()
# these don't produce data... yet.
# TODO: the config hasn't been read yet, so these need to be configurable!
non_config_files = ['arx.json', 'cam.json', 'ebs.json', 'mot.json']
mapAgg.configure('map.json', non_config_files=non_config_files)

from src.map.lib.NodeRunner import NodeRunner

node = NodeRunner()
node.configure('map.json')

map_bp = Blueprint(
        'map_bp', __name__, subdomain='map',
        template_folder=mapAgg.config['TEMPLATE_FOLDER'],
        static_folder=mapAgg.config['STATIC_FOLDER'],
        static_url_path=mapAgg.config['STATIC_FOLDER']
)


@map_bp.route('/', subdomain='map')
def index():
    return redirect("/map", code=302)


@map_bp.route("/map", methods=['GET'], subdomain='map')
def map():
    return render_template(mapAgg.config['MAP_TEMPLATE'])


@map_bp.route("/aggregated", methods=['GET'], subdomain='map')
def aggregated():
    """  returns all aggregated data """
    return mapAgg.aggregated


@map_bp.route("/aggregated/<mod>", methods=['GET'], subdomain='map')
def aggregated_by_module(mod):
    """ returns module speccific aggregated data"""
    return mapAgg.aggregated[mod]


@map_bp.route("/config/<mod>", methods=['GET'], subdomain='map')
def config_for_module(mod):
    """ returns module specific config"""
    return mapAgg.configs[mod]


@map_bp.route("/aggregated/<mod>/<context>", methods=['GET'], subdomain='map')
def aggregated_by_module_context(mod, context):
    """ redirect to a specific context of a module """
    return redirect('http://' + mod + '.' + mapAgg.configs[mod]['SERVER_NAME'] + '/' + context, code=302)


@map_bp.route('/reload/<mod>', subdomain='map')
def reload(mod):
    if mapAgg.reload(mod):
        return "OK", 200
    return "FAIL", 500


@map_bp.route('/unload/<mod>', subdomain='map')
def unload(mod):
    if mapAgg.unload(mod):
        return "OK", 200
    return "FAIL", 500
