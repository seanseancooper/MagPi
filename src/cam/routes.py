import json

from flask import Blueprint, render_template, redirect, jsonify, Response

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
    return render_template("cam.html.j2",
                           config=camMgr.config,
                           plugin=camMgr.plugin)


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
    return jsonify(camMgr.get_plugin_stats())


@cam_bp.route('/stats/tracker', methods=['GET'], subdomain='cam')
def cam_stats_tracker():
    return jsonify(camMgr.get_tracker_stats())


@cam_bp.route('/stream')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(camMgr.plugin.stream_direct(),
                    mimetype='multipart/x-mixed-replace; boundary=--jpgboundary')

