from flask import Blueprint, redirect, render_template, jsonify

from src.map.MAPAggregator import MAPAggregator
mapAgg = MAPAggregator()
# TODO: the config hasn't been read yet, how can these be configurable?
non_config_files = ['arx.json', 'cam.json', 'ebs.json', 'gps.json', 'view.json']
mapAgg.configure('map.json', non_config_files=non_config_files)

from src.gps.GPSRetriever import GPSRetriever
gpsRet = GPSRetriever()
gpsRet.configure('gps.json')

from src.lib.NodeRunner import NodeRunner
# node map service on :5173
map_node = NodeRunner()
map_node.configure('map.json')

# node js_gps_ret service on :5014
gps_node = NodeRunner()
gps_node.configure('map.json')

map_bp = Blueprint(
        'map_bp', __name__, subdomain='map',
        template_folder=mapAgg.config['TEMPLATE_FOLDER'],
        static_folder=mapAgg.config['STATIC_FOLDER'],
        static_url_path=mapAgg.config['STATIC_FOLDER']
)


@map_bp.route('/', subdomain='map')
def index():
    return redirect("/data", code=302)


@map_bp.route("/map", methods=['GET'], subdomain='map')
def map():
    return render_template(mapAgg.config['MAP_TEMPLATE'])


@map_bp.route('/stats', methods=['GET'], subdomain='map')
def map_stats():
    from src.lib.utils import format_time, format_delta
    stats = {
        'created': format_time(mapAgg.created, "%H:%M:%S"),
        'updated': format_time(mapAgg.updated, "%H:%M:%S"),
        'elapsed': format_delta(mapAgg.elapsed, "%H:%M:%S"),
    }
    return jsonify(stats)


@map_bp.route("/data", methods=['GET'], subdomain='map')
def aggregated():
    """  returns all aggregated data """
    return mapAgg.module_data


@map_bp.route("/data/<mod>", methods=['GET'], subdomain='map')
def aggregated_by_module(mod):
    """ returns module specific aggregated data"""
    return mapAgg.module_data[mod]


@map_bp.route("/data/<mod>/<context>", methods=['GET'], subdomain='map')
def aggregated_by_module_context(mod, context):
    """ redirect to a specific context of a module """
    return redirect('http://' + mod + '.' + mapAgg.module_configs[mod]['SERVER_NAME'] + '/' + context, code=302)



@map_bp.route("/position", methods=['GET'], subdomain="map")
def gps_position():
    """  return entire result """
    return gpsRet.gps_result()


@map_bp.route('/stats', methods=['GET'], subdomain='gps')
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


@map_bp.route("/location", methods=['GET'], subdomain="map")
def gps_location():
    """ return lat, lon """
    return gpsRet.gps_location()


@map_bp.route("/time", methods=['GET'], subdomain="map")
def gps_time():
    """ return formatted time 2024-12-06 12:27:50.185321 """
    return gpsRet.gps_time()


@map_bp.route("/altitude", methods=['GET'], subdomain="map")
def gps_altitude():
    return gpsRet.gps_altitude()


@map_bp.route("/speed", methods=['GET'], subdomain="map")
def gps_speed():
    return gpsRet.gps_speed()


@map_bp.route("/track", methods=['GET'], subdomain="map")
def gps_track():
    return gpsRet.gps_track()


@map_bp.route("/heading", methods=['GET'], subdomain="map")
def gps_heading():
    return gpsRet.gps_heading()


@map_bp.route("/climb", methods=['GET'], subdomain="map")
def gps_climb():
    return gpsRet.gps_climb()


@map_bp.route("/config", methods=['GET'], subdomain="map")
def gps_config():
    return gpsRet.config


@map_bp.route("/<BSSID>/triltaterate", methods=['GET'], subdomain='map')
def gps_trilaterate(BSSID):
    # instance and start a Trilaterator
    from src.map.lib.Trilaterator import Trilaterator

    trilaterator = Trilaterator()
    trilaterator.set_target(BSSID)
    trilaterator.run()
    return trilaterator.result
