# Version: 1.1.0
# Description: RabbitMQ producer for sending FrameObjekt instances as JSON messages.
# Uses pika for RabbitMQ communication.
# Message persistence enabled for reliability.
# Logging added for better monitoring and debugging.
from datetime import datetime

import pika
import json
import logging


class RabbitMQProducer:

    def __init__(self, queue):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.queue = queue
        self.channel.queue_declare(queue=self.queue, durable=True)

    def publish_message(self, message):
        """Send FrameObjekt data to RabbitMQ."""
        try:
            # dictObject['created'] = datetime.now().isoformat()
            # message = json.dumps(dictObject)
            self.channel.basic_publish(
                exchange='',
                routing_key=self.queue,
                body=message,
                # body=bytes(dictObject, encoding='latin-1'),
                properties=pika.BasicProperties(
                        delivery_mode=2  # Make message persistent
                )
            )
            logging.info(f"Sent message successfully")
        except Exception as e:
            logging.error(f"Failed to send message: {e}")
