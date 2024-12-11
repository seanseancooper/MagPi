import json

from flask import Blueprint, render_template, redirect

from src.cam.CAMManager import CAMManager

camMgr = CAMManager()
camMgr.configure('cam.json')

cam_bp = Blueprint(
        'cam_bp', __name__, subdomain='cam',
        template_folder=camMgr.config['TEMPLATE_FOLDER'],
        static_folder=camMgr.config['STATIC_FOLDER'],
        static_url_path='/static'
)


@cam_bp.route('/')
def index():
    # TODO: what 'data' can be exposed instead of config?
    #  capture stats
    #  plugin config
    #  tracking hyperparameter config
    #  tag
    #  tag location
    #  self._ml = []                        # DO NOT CHANGE: list of (x,y) location of contour in self.contours
    #  self._frame_delta                    # DO NOT CHANGE: euclidean distance between the current and previous frames
    #  self._frame_MSE = float()
    #  self._frame_SSIM = float()
    #  motion detected
    #  analytics: last n frames
    plugin = camMgr.plugin.get()
    tracker = camMgr.plugin.tracker.get()
    streamservice = camMgr.plugin.streamservice.get()
    return plugin, tracker, streamservice


@cam_bp.route("/ctrl", methods=['GET'], subdomain='cam')
def cam_controller():
    return render_template("cam_controller.html.j2", plugin=camMgr.plugin)


@cam_bp.route("/snap", methods=['POST'], subdomain='cam')
def cam_snap():
    camMgr.plugin.cam_snap()


@cam_bp.route("/view/<direction>", methods=['GET', 'POST'], subdomain='cam')
def cam_direction(direction):
    camMgr.cam_reload(direction)


@cam_bp.route("/multibutton/<mode>", methods=['POST'], subdomain='cam')
def cam_multibutton(mode):
    return camMgr.cam_multibutton(mode)


@cam_bp.route("/plugin/<field>/<value>", methods=['POST'], subdomain='cam')
def cam_plugin(field, value):
    if camMgr.set_plugin_field(field, value):
        return "OK"
    return "FAIL"


