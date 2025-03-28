from flask import Blueprint, render_template


net_bp = Blueprint(
        'net_bp', __name__, subdomain='net',
        # template_folder=s.config['TEMPLATE_FOLDER'],
        # static_folder=s.config['STATIC_FOLDER'],
        static_url_path='/static'
)


@net_bp.route('/', subdomain="net")
def index():
    return render_template("net.html.j2")
