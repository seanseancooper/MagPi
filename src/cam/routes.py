import json

from flask import Blueprint, render_template, redirect, jsonify

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
    return redirect('/config', 302)


@cam_bp.route("/ctrl", methods=['GET'], subdomain='cam')
def cam_controller():
    return render_template("cam_controller.html.j2", plugin=camMgr.plugin)


@cam_bp.route("/snap", methods=['POST'], subdomain='cam')
def cam_snap():
    return camMgr.plugin.cam_snap()


@cam_bp.route("/view/<direction>", methods=['GET', 'POST'], subdomain='cam')
def cam_direction(direction):
    return camMgr.cam_reload(direction)


@cam_bp.route("/multibutton/<mode>", methods=['POST'], subdomain='cam')
def cam_multibutton(mode):
    return camMgr.cam_multibutton(mode)


@cam_bp.route("/plugin/<field>/<value>", methods=['POST'], subdomain='cam')
def cam_plugin(field, value):
    if camMgr.set_plugin_field(field, value):
        return "OK"
    return "FAIL"


@cam_bp.route('/config', methods=['GET'], subdomain='cam')
def cam_config():
    return jsonify(camMgr.config)


@cam_bp.route('/stats', methods=['GET'], subdomain='cam')
def cam_stats():

    _stats = camMgr.plugin.get()
    _stats['tracker'] = camMgr.plugin.tracker.get()

    return jsonify(_stats)

