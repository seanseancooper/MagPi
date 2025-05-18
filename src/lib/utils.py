import os
import uuid
from datetime import datetime
from string import Template
import logging

logger_root = logging.getLogger('root')
speech_logger = logging.getLogger('speech_logger')
gps_logger = logging.getLogger('gps_logger')

def generate_uuid():
    return uuid.uuid4()

def mute(mutable):
    ''' mutes/unmutes object passed into it '''
    mutable.is_mute = not mutable.is_mute
    mutable.updated = datetime.now()
    return mutable.is_mute

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
