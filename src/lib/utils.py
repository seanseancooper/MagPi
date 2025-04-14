import os
import shutil
import subprocess
from datetime import datetime
from string import Template
import requests
import json
import logging

logger_root = logging.getLogger('root')
speech_logger = logging.getLogger('speech_logger')
gps_logger = logging.getLogger('gps_logger')


def mute(mutable):
    ''' mutes/unmutes object passed into it '''
    mutable.is_mute = not mutable.is_mute
    mutable.updated = datetime.now()
    return mutable.is_mute


def time_traveller(o):
    ''' experiment: mutate object AND provide data to caller '''

    o.updated = datetime.now()
    o.elapsed = o.updated - o.created

    map = {
        'updated': o.updated,
        'elapsed': o.elapsed,
    }

    return o.elapsed, map


def enunciate(speakable, message):
    if not speakable.is_mute:
        speakable.speaker.broadcast(f"{message}")

    if speakable.DEBUG:
        logger_root.debug(f"[{__name__}]:{message}")


def format_time(_, fmt):
    return f'{_.strftime(fmt)}'


def format_delta(_, fmt):
    # https://stackoverflow.com/questions/8906926/formatting-timedelta-objects

    class DeltaTemplate(Template):
        delimiter = "%"

        def formats_delta(tdelta, fmt):
            d = {"D": tdelta.days}
            hours, rem = divmod(tdelta.seconds, 3600)
            minutes, seconds = divmod(rem, 60)
            d["H"] = '{:02d}'.format(hours)
            d["M"] = '{:02d}'.format(minutes)
            d["S"] = '{:02d}'.format(seconds)
            t = DeltaTemplate(fmt)
            return t.substitute(**d)

    return DeltaTemplate.formats_delta(_, fmt)


def make_path(outdir):
    PATH = os.path.join(os.getcwd(), outdir)
    if not os.path.exists(PATH):
        os.makedirs(PATH)


def write_file(path, filename, message, mode):
    with open(os.path.join(path, filename), mode) as outfile:
        outfile.write(f"{message}\n")
        return True


def read_file(path, filename, mode):
    with open(os.path.join(path, filename), mode) as infile:
        return infile.read()


def runOSCommand(command: list):
    try:
        command[0] = shutil.which(command[0])
        ps = subprocess.Popen(command)
        logger_root.debug(f"[{__name__}]: PID --> {ps.pid}")
        return ps.pid
    except OSError as e:
        logger_root.fatal(f"[{__name__}]:couldn't create a process for \'{command}\': {e}")
    return 0


def get_location(locator):
    """ gets location from GPS endpoint"""
    try:
        resp = requests.get(locator.config.get('GPS_ENDPOINT', 'http://gps.localhost:5004/position'))
        position = json.loads(resp.text)
        locator.lat = position.get('LATITUDE', position.get('lat'))
        locator.lon = position.get('LONGITUDE', position.get('lon'))
    except Exception as e:
        speech_logger.warning(f"GPS Error")
        gps_logger.warning(f"GPS Retrieval Error: {e}")


def write_to_scanlist(config, searchmap):
    """Write current searchmap out as JSON"""
    make_path(config.get('OUTFILE_PATH', "out"))
    _time = datetime.now().strftime(config.get('DATETIME_FORMAT', "%Y%m%d_%H%M%S"))
    if len(searchmap) > 0:  # don't write nothing; write something.
        # todo: process this as above....
        return write_file(config['OUTFILE_PATH'], "scanlist_" + _time + ".json", json.dumps(searchmap, indent=1), "x")

def print_table(table):
    # Functional black magic.
    widths = list(map(max, map(lambda l: map(len, l), zip(*table))))

    justified_table = []
    for line in table:
        justified_line = []
        for i, el in enumerate(line):
            try:
                if isinstance(el, str):
                    justified_line.append(el.ljust(widths[i] + 2))
                if isinstance(el, list):
                    pass  # don't deal with lists of signal_cache
            except AttributeError:
                pass  # I got an 'el' that doesn't 'justify'

        justified_table.append(justified_line)

    for line in justified_table:
        print("\t".join(line))

def print_signals(sgnls, columns):
    table = [columns]

    def print_signal(sgnl):
        sgnl_properties = []

        def make_cols(column):
            try:
                # make boolean a str to print (needs 'width').
                if isinstance(sgnl[column], bool):
                    sgnl_properties.append(str(sgnl[column]))
                else:
                    sgnl_properties.append(sgnl[column])
            except KeyError as e:
                print(f"KeyError getting column for {e}")

        [make_cols(column) for column in columns]
        table.append(sgnl_properties)

    [print_signal(sgnl) for sgnl in sgnls]
    print_table(table)
