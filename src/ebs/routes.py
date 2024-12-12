from flask import Blueprint

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
    return ebsMgr.run()


@ebs_bp.route('/run', methods=['GET', 'POST'])
def ebs_run():
    return ebsMgr.run()


@ebs_bp.route('/enunciate/<msg>', methods=['GET', 'POST'])
def ebs_enunciate(msg):
    ebsMgr.enunciate(msg)
    return "OK"


@ebs_bp.route("/stop", methods=['GET', 'POST'])
def ebs_stop():
    return ebsMgr.ebs_stop()
