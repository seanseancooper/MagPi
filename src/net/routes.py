from flask import Blueprint, render_template
from src.config import readConfig

config = {}
readConfig('net.json', config)

net_bp = Blueprint(
        'net_bp', __name__, subdomain='net',
        # template_folder=s.config['TEMPLATE_FOLDER'],
        # static_folder=s.config['STATIC_FOLDER'],
        static_url_path='/static'
)

@net_bp.route('/', subdomain="net")
def index():
    return render_template("net.html.j2", dashboardURL=config['ELASTIC_DASHBOARD_URL'])

# note: there is *anticipated* to be an elasticc.pull() method.
