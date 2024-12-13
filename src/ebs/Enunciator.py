import logging
import queue
import threading
import time

from src.wifi.lib.TokenBucket import TokenBucket
from src.config import readConfig

logger_root = logging.getLogger('root')
ebs_logger = logging.getLogger('ebs_logger')


class Enunciator(threading.Thread):
    """ Enunciator speaks its' mind... """

    # Enunciator: Provide auditory feedback on events. This passes
    # a message to a local queue, then passed an interface queue
    # for a SpeechService implementation, which will render it.

    def __init__(self, name, tokens, interval):
        super().__init__()
        self.name = name
        self.tokens = tokens
        self.interval = interval
        self.speechservice = None
        self.config = {}
        self.message_queue = None                        # the message queue
        self.throttle = None
        self.debug = False

        self.loop_polling_interval = 1.0
        self.limit = 0

        self.running_actuator = False

    def stop(self):
        msg = "Speech Actuator Service off line"
        logger_root.info(msg)

        if self.message_queue:
            # TODO: this is a thread...
            self.message_queue.empty()
            self.message_queue.shutdown()
            logger_root.info(f"Speech Actuator Service offline {self.message_queue}")

    def configure(self):
        readConfig('ebs.json', self.config)
        self.throttle = TokenBucket(int(self.tokens), int(self.interval))
        self.debug = self.config.get('DEBUG', False)
        self.limit = self.config.get('ENUNCIATOR_MSG_LIMIT', 10)
        self.loop_polling_interval = self.config.get('ENUNCIATOR_LOOP_POLLING_INTERVAL', 0.5)

    def init(self):
        self.message_queue = queue.Queue(maxsize=self.limit)  # make configurable
        self.speechservice.make_fifo()

    def actuate(self):
        """ gets message on queue to SpeechService"""
        while self.speechservice:
            self.running_actuator = True
            if not self.message_queue.empty():
                try:
                    # enqueue message to SpeechService.
                    message = self.message_queue.get()
                    self.speechservice.enqueue(message)
                    ebs_logger.debug(f'actuator: {message}')
                except Exception as e:
                    logger_root.error(f'Exception: {e}')
            else:
                time.sleep(self.loop_polling_interval)

    def broadcast(self, message):
        """ puts message on queue the method clients use to enqueue messages. """
        if message:
            if self.running_actuator:
                try:
                    # push message to onto local fifo
                    self.message_queue.put(message)
                    ebs_logger.debug(f'broadcast: {message}')
                except Exception as e:
                    logger_root.error(f'Exception:  {e}')
            else:
                logger_root.error('Actuator not running')


    def ebs_messsage(self, message):
        """ Broadcast a message using the EBS speech service"""

        if self.throttle.handle(message):
            # handle(mesg) returned the message if 'able'
            self.broadcast(message)

    def run(self):
        self.actuate()

