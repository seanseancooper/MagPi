import os
from flask import Blueprint, redirect, render_template
from src.config import CONFIG_PATH, readConfig

config = {}
readConfig(os.path.join(CONFIG_PATH, 'map.json'), config)

from src.map.MAPAggregator import MAPAggregator

mapAgg = MAPAggregator()
mapAgg.configure(os.path.join(CONFIG_PATH, 'map.json'))

from src.map.lib.NodeRunner import NodeRunner

node = NodeRunner()
node.configure(os.path.join(CONFIG_PATH, 'map.json'))

map_bp = Blueprint(
        'map_bp', __name__, subdomain='map',
        template_folder=config['TEMPLATE_FOLDER'],
        static_folder=config['STATIC_FOLDER'],
        static_url_path=config['STATIC_FOLDER']
)


@map_bp.route('/', subdomain='map')
def index():
    return redirect("/map", code=302)


@map_bp.route("/map", methods=['GET'], subdomain='map')
def map():
    return render_template(config['MAP_TEMPLATE'])


@map_bp.route("/aggregated", methods=['GET'], subdomain='map')
def aggregated():
    return mapAgg.aggregated


@map_bp.route("/aggregated/<mod>", methods=['GET'], subdomain='map')
def aggregated_by_module(mod):
    return mapAgg.aggregated[mod]


@map_bp.route("/aggregated/<mod>/<context>", methods=['GET'], subdomain='map')
def aggregated_by_module_context(mod, context):
    return redirect('http://' + mod.lower() + '.' + mapAgg.configs[mod]['SERVER_NAME'] + '/' + context, code=302)


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
