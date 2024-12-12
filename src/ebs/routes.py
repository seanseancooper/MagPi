from flask import Blueprint, render_template, request

from src.ebs.EBSManager import EBSManager

ebsMgr = EBSManager()
ebsMgr.configure('ebs.json')


ebs_bp = Blueprint(
        'ebs_bp', __name__, subdomain='ebs',
        template_folder=ebsMgr.config['TEMPLATE_FOLDER'],
        static_folder=ebsMgr.config['STATIC_FOLDER'],
)


@ebs_bp.route('/', subdomain='ebs')
def index():
    return ebsMgr.config


@ebs_bp.route('/enunciate', methods=['GET', 'POST'], subdomain='ebs')
def ebs_enunciate():

    if request.method == 'POST':
        # result = request.form
        # json_result = dict(result)
        msg = request.form.get("msg", "")

        if msg:
           ebsMgr.enunciate(str(msg))

    return render_template("ebs.html.j2")


@ebs_bp.route('/run', methods=['GET', 'POST'], subdomain='ebs')
def ebs_run():
    return ebsMgr.run()


@ebs_bp.route("/stop", methods=['GET', 'POST'], subdomain='ebs')
def ebs_stop():
    return ebsMgr.stop()
