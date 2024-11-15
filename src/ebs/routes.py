import os
from flask import Blueprint

from src.ebs.EBSManager import EBSManager
from src.config import CONFIG_PATH

ebsMgr = EBSManager()
ebsMgr.configure(os.path.join(CONFIG_PATH, 'ebs.json'))

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


@ebs_bp.route("/stop", methods=['GET', 'POST'])
def ebs_stop():
    return ebsMgr.ebs_stop()
