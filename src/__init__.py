from flask import Blueprint, render_template

root_bp = Blueprint(
        'root_bp', __name__,
        template_folder='templates',
        static_folder='static',
        static_url_path='/static'
)


@root_bp.route('/')
def index():
    return render_template("index.html.j2")

