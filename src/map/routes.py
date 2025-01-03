from flask import Blueprint, redirect, render_template, jsonify

from src.map.MAPAggregator import MAPAggregator

mapAgg = MAPAggregator()
# TODO: the config hasn't been read yet, how can these be configurable?
non_config_files = ['arx.json', 'ebs.json', 'mot.json']
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
    return redirect("/aggregated", code=302)


@map_bp.route("/map", methods=['GET'], subdomain='map')
def map():
    return render_template(mapAgg.config['MAP_TEMPLATE'])


@map_bp.route('/stats', methods=['GET'], subdomain='map')
def map_stats():
    from src.lib.utils import format_time, format_delta
    stats = {
        'created': format_time(mapAgg.created, "%H:%M:%S"),
        'updated': format_time(mapAgg.updated, "%H:%M:%S"),
        'elapsed': format_delta(mapAgg.elapsed, "%H:%M:%S"),
    }
    return jsonify(stats)


@map_bp.route("/aggregated", methods=['GET'], subdomain='map')
def aggregated():
    """  returns all aggregated data """
    return mapAgg.module_aggregated

    # TODO: move to manager
    # _configs = mapAgg.module_configs
    # _configs['stats'] = mapAgg.module_stats
    # return jsonify(_configs)


@map_bp.route("/aggregated/<mod>", methods=['GET'], subdomain='map')
def aggregated_by_module(mod):
    """ returns module specific aggregated data"""
    return mapAgg.module_aggregated[mod]
    # _configs = mapAgg.module_configs[mod]
    # _configs['stats'] = mapAgg.module_stats[mod]
    # return jsonify(_configs)


@map_bp.route("/aggregated/<mod>/<context>", methods=['GET'], subdomain='map')
def aggregated_by_module_context(mod, context):
    """ redirect to a specific context of a module """
    return redirect('http://' + mod + '.' + mapAgg.module_configs[mod]['SERVER_NAME'] + '/' + context, code=302)

