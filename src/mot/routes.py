import os
from flask import Blueprint, redirect

from src.mot.MOTManager import MOTManager
from src.config import CONFIG_PATH

motMgr = MOTManager()
motMgr.configure(os.path.join(CONFIG_PATH, 'mot.json'))

mot_bp = Blueprint(
        'mot_bp', __name__, subdomain='mot',
        template_folder=motMgr.config['TEMPLATE_FOLDER'],
        static_folder=motMgr.config['STATIC_FOLDER'],
)


@mot_bp.route('/')
def index():
    return redirect("/controlpanel", code=302)


@mot_bp.route("/stop", methods=['GET', 'POST'])
def motion_stop():
    return motMgr.mot_stop()


# NOTE: MOT has a control panel of it's own
@mot_bp.route("/controlpanel", methods=['GET'])
def motion_controlpanel():
    return redirect(motMgr.motion_controlpanel(), code=302)

