import logging
import queue
import threading
import time

from src.wifi.lib.TokenBucket import TokenBucket
from src.config import readConfig

logger_root = logging.getLogger('root')


class Enunciator(threading.Thread):
    """ Enunciator speaks its' mind... """

    # Enunciator: Provide auditory feedback on events. This will pass
    # a message to a queue which is read by an interface for a
    # SpeechService, which will render it.

    def __init__(self, name, tokens, interval):
        super().__init__()
        self.name = name
        self.tokens = tokens
        self.interval = interval
        self.speech = None
        self.config = {}
        self.message_queue = None                        # the message queue
        self.throttle = None
        self.debug = False

        self.loop_polling_interval = 1.0
        self.limit = 10

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

    def init(self):
        self.message_queue = queue.Queue(maxsize=self.limit)  # make configurable
        self.speech.make_fifo()

    def actuate(self):
        """ gets message on queue to SpeechService"""
        while True:
            self.running_actuator = True
            if not self.message_queue.empty():
                message = self.message_queue.get()

                logger_root.info(f'actuator: {message} {self.message_queue.qsize()}')

                try:
                    # enqueue message to SpeechService.
                    self.speech.enqueue(message)
                    pass
                except Exception as e:
                    logger_root.error(f'Exception: {e}')

            else:
                time.sleep(self.loop_polling_interval)


    def broadcast(self, message):
        """ puts message on queue the method clients use to enqueue messages. """
        if message:
            if self.running_actuator:

                logger_root.info(f'broadcast: {message}')

                try:
                    # push message to onto local fifo
                    self.message_queue.put(message)
                except Exception as e:
                    logger_root.error(f'Exception:  {e}')
            else:
                logger_root.error('Actuator Service not running')


    def ebs_messsage(self, message):
        """ Broadcast a message using the EBS speech service"""

        if self.throttle.handle(message):
            # handle(mesg) returned the message if 'able'
            self.broadcast(message)

    def run(self):
        self.actuate()

