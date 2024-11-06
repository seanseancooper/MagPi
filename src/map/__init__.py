import os
from flask import Blueprint, redirect, render_template
from src.config import CONFIG_PATH, readConfig

config = {}
readConfig(os.path.join(CONFIG_PATH, 'map.json'), config)

from src.map.lib.NodeRunner import NodeRunner
node = NodeRunner()
node.configure(os.path.join(CONFIG_PATH, 'map.json'))

map_bp = Blueprint(
        'map_bp', __name__, subdomain='map',
        template_folder=config['TEMPLATE_FOLDER'],
        static_folder=config['STATIC_FOLDER'],
        static_url_path=config['STATIC_FOLDER']
)


@map_bp.route('/')
def index():
    return redirect("/map", code=302)


@map_bp.route("/map", methods=['GET'])
def map():
    return render_template(config['MAP_TEMPLATE'])

