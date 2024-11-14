import os
from datetime import datetime
import logging

logger_root = logging.getLogger('root')


def mute(mutable):
    ''' mutes/unmutes object passed into it '''
    mutable.is_mute = not mutable.is_mute
    mutable.updated = datetime.now()
    return mutable.is_mute


def enunciate(speakable, message):
    if not speakable.is_mute:
        speakable.speaker.broadcast(f"{message}")

    if speakable.DEBUG:
        logger_root.debug(f"[{__name__}]:{message}")


def format_time(_, fmt):
    return f'{_.strftime(fmt)}'


def format_delta(_, fmt):
    return f'{_.strptime(fmt)}'


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


