import os
import logging

from src.wifi.lib.TokenBucket import TokenBucket

logger_root = logging.getLogger('root')


class Enunciator:
    """ Enunciator speaks its' mind... """

    def __init__(self, name, tokens, interval):
        self.name = name
        self.tokens = tokens
        self.interval = interval
        self.config = {}
        self.fifo = None
        self.throttle = None
        self.debug = False

    def configure(self):

        self.fifo = self.config.get('FIFO_PATH', os.environ.get('FIFO_PATH', 'scanner.fifo'))
        self.throttle = TokenBucket(int(self.tokens), int(self.interval))
        self.debug = self.config.get('DEBUG', False)

    def broadcast(self, message):
        """ Broadcast a message using the EBS speech service"""

        if self.throttle.handle(message):
            # handle(mesg) returned the message if 'able'
            try:
                if os.path.exists(self.fifo):
                    import stat
                    if stat.S_ISFIFO(os.stat(self.fifo).st_mode):
                        with open(self.fifo, "w") as f:
                            f.write(str(message) + "\n")
                            if self.debug:
                                logger_root.debug(f"[{__name__}]: sent \"{message}\" message to FIFO")
                else:
                    logger_root.warning(
                        f"[{__name__}]: Failed to get FIFO (EBS offline?): Aborted message \"{message}\"")
            except Exception as e:
                logger_root.error(f"[{__name__}]:Exception {e} occurred: Stale FIFO? Aborted message \"{message}\"")
