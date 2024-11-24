import os
from flask import Blueprint, render_template, redirect

from src.cam.CAMManager import CAMManager
from src.config import CONFIG_PATH

camMgr = CAMManager()
camMgr.configure(os.path.join(CONFIG_PATH, 'cam.json'))

cam_bp = Blueprint(
        'cam_bp', __name__, subdomain='cam',
        template_folder=camMgr.config['TEMPLATE_FOLDER'],
        static_folder=camMgr.config['STATIC_FOLDER'],
        static_url_path='/static'
)


@cam_bp.route('/')
def index():
    return redirect("/ctrl", code=302)


@cam_bp.route("/ctrl", methods=['GET'], subdomain='cam')
def cam_controller():
    return render_template("cam_controller.html.j2", plugin=camMgr.plugin)


@cam_bp.route("/snap", methods=['POST'], subdomain='cam')
def cam_snap():
    camMgr.plugin.cam_snap()
    return "OK"


@cam_bp.route("/view/<direction>", methods=['GET', 'POST'], subdomain='cam')
def cam_direction(direction):
    camMgr.cam_reload(direction)
    return "OK"


@cam_bp.route("/multibutton/<mode>", methods=['POST'], subdomain='cam')
def cam_multibutton(mode):
    camMgr.cam_multibutton(mode)
    return "OK"


@cam_bp.route("/plugin/<field>/<value>", methods=['POST'], subdomain='cam')
def cam_plugin(field, value):
    if camMgr.cam_twiddle(field, value):
        return "OK"
    return "FAIL"


@cam_bp.route("/tracker/<field>/<value>", methods=['POST'], subdomain='cam')
def cam_tracker(field, value):
    if camMgr.tracker_twiddle(field, value):
        return "OK"
    return "FAIL"


@cam_bp.route("/move/<command>")
def cam_move(command):
    part = command.split("&")
    command = {
        "S_0": part[0].replace("S_0=", ""),
        "S_1": part[1].replace("S_1=", ""),
        "E_0": part[2].replace("E_0=", ""),
        "E_1": part[3].replace("E_1=", "")
    }

    return camMgr.ircam_move(command)



