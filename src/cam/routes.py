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
    from src.lib.utils import format_time, format_delta

    p_stats = {

        "_area": str(camMgr.plugin._area),
        "_max_height": str(camMgr.plugin._max_height),
        "_max_width": str(camMgr.plugin._max_width),

        "has_symbols": camMgr.plugin.has_symbols,
        "has_analysis": camMgr.plugin.has_analysis,
        "has_motion": camMgr.plugin.has_motion,

        "_kz": str(camMgr.plugin._kz),
        "threshold": camMgr.plugin.threshold,
        "show_threshold": camMgr.plugin.show_threshold,
        "mediapipe": camMgr.plugin.mediapipe,
        "tracked": [_ for _ in camMgr.plugin.tracked]

    }

    t_stats = camMgr.plugin.tracker.get()

    return jsonify(t_stats)

