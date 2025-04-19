from flask import Blueprint, redirect, jsonify

from src.gps.GPSRetriever import GPSRetriever

gpsRet = GPSRetriever()
gpsRet.configure('gps.json')

# node js_gps_ret service on :3000
from src.lib.NodeRunner import NodeRunner
node = NodeRunner()
node.configure('map.json')


gps_bp = Blueprint(
        'gps_bp', __name__, subdomain='gps',
        template_folder=gpsRet.config['TEMPLATE_FOLDER'],
        static_folder=gpsRet.config['STATIC_FOLDER'],
        static_url_path='/static'
)


@gps_bp.route('/', subdomain="gps")
def index():
    return redirect("/position", code=302)


@gps_bp.route("/position", methods=['GET'], subdomain="gps")
def gps_position():
    """  return entire result """
    return gpsRet.gps_result()


@gps_bp.route('/stats', methods=['GET'], subdomain='gps')
def gps_stats():
    from src.lib.utils import format_time, format_delta

    # placeholder; this should already be a map called stats in s. I want to be able to add to that map adhoc.
    stats = {
        'created'       : format_time(gpsRet.created, "%H:%M:%S"),
        'updated'       : format_time(gpsRet.updated, "%H:%M:%S"),
        'elapsed'       : format_delta(gpsRet.elapsed, "%H:%M:%S"),
        'polling_count' : gpsRet.polling_count,
        'lat'           : gpsRet.result['lat'],
        'lon'           : gpsRet.result['lon']
    }
    return jsonify(stats)


@gps_bp.route("/location", methods=['GET'], subdomain="gps")
def gps_location():
    """ return lat, lon """
    return gpsRet.gps_location()


@gps_bp.route("/time", methods=['GET'], subdomain="gps")
def gps_time():
    """ return formatted time 2024-12-06 12:27:50.185321 """
    return gpsRet.gps_time()


@gps_bp.route("/altitude", methods=['GET'], subdomain="gps")
def gps_altitude():
    return gpsRet.gps_altitude()


@gps_bp.route("/speed", methods=['GET'], subdomain="gps")
def gps_speed():
    return gpsRet.gps_speed()


@gps_bp.route("/track", methods=['GET'], subdomain="gps")
def gps_track():
    return gpsRet.gps_track()


@gps_bp.route("/heading", methods=['GET'], subdomain="gps")
def gps_heading():
    return gpsRet.gps_heading()


@gps_bp.route("/climb", methods=['GET'], subdomain="gps")
def gps_climb():
    return gpsRet.gps_climb()


@gps_bp.route("/config", methods=['GET'], subdomain="gps")
def gps_config():
    return gpsRet.config

