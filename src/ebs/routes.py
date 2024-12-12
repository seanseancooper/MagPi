from flask import Blueprint, redirect

from src.ebs.EBSManager import EBSManager

ebsMgr = EBSManager()
ebsMgr.configure('ebs.json')


ebs_bp = Blueprint(
        'ebs_bp', __name__, subdomain='ebs',
        template_folder=ebsMgr.config['TEMPLATE_FOLDER'],
        static_folder=ebsMgr.config['STATIC_FOLDER'],
)


@ebs_bp.route('/')
def index():
    return redirect('/enunciate/hello', code=302)


@ebs_bp.route('/run', methods=['GET', 'POST'])
def ebs_run():
    return ebsMgr.run()


@ebs_bp.route('/enunciate/<msg>', methods=['GET', 'POST'])
def ebs_enunciate(msg):
    # TODO: make sure this is only ever a string!!
    # TODO: form & POST only
    ebsMgr.enunciate(msg)
    return "OK"


@ebs_bp.route("/stop", methods=['GET', 'POST'])
def ebs_stop():
    return ebsMgr.stop()
