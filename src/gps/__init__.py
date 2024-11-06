import os
from flask import Blueprint, redirect, render_template

from src.gps.GPSRetriever import GPSRetriever
from src.config import CONFIG_PATH

gpsRet = GPSRetriever()
gpsRet.configure(os.path.join(CONFIG_PATH, 'gps.json'))

gps_bp = Blueprint(
        'gps_bp', __name__, subdomain='gps',
        template_folder=gpsRet.config['TEMPLATE_FOLDER'],
        static_folder=gpsRet.config['STATIC_FOLDER'],
        static_url_path='/static'
)


@gps_bp.route('/', subdomain="gps")
def index():
    return redirect("/position", code=302)


@gps_bp.route("/time", methods=['GET'], subdomain="gps")
def gps_time():
    return gpsRet.gps_time()


@gps_bp.route("/position", methods=['GET'], subdomain="gps")
def gps_position():
    return gpsRet.gps_position()


@gps_bp.route("/location", methods=['GET'], subdomain="gps")
def gps_location():
    return gpsRet.gps_location()


@gps_bp.route("/altitude", methods=['GET'], subdomain="gps")
def gps_altitude():
    return gpsRet.gps_altitude()


@gps_bp.route("/speed", methods=['GET'], subdomain="gps")
def gps_speed():
    return gpsRet.gps_speed()


@gps_bp.route("/heading", methods=['GET'], subdomain="gps")
def gps_heading():
    return gpsRet.gps_track()


@gps_bp.route("/climb", methods=['GET'], subdomain="gps")
def gps_climb():
    return gpsRet.gps_climb()
