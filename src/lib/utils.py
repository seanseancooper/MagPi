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


def make_path(outdir):
    PATH = os.path.join(os.getcwd(), outdir)
    if not os.path.exists(PATH):
        os.makedirs(PATH)


def write_file(path, filename, message, mode):
    # TODO: is this the only thing that writes files???
    with open(os.path.join(path, filename), mode) as outfile:
        outfile.write(f"{message}\n")


