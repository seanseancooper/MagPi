# Version: 1.1.0
# Description: RabbitMQ producer for sending FrameObjekt instances as JSON messages.
# Uses pika for RabbitMQ communication.
# Message persistence enabled for reliability.
# Logging added for better monitoring and debugging.

import pika
import json
import logging
from src.net.lib.net_utils import frameobjekt_to_dict


class RabbitMQProducer:

    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='frame_queue', durable=True)

    def publish_message(self, frame_obj):
        """Send FrameObjekt data to RabbitMQ."""
        try:
            message = json.dumps(frameobjekt_to_dict(frame_obj))
            self.channel.basic_publish(
                exchange='',
                routing_key='frame_queue',
                body=bytes(message, encoding='utf_8'),
                properties=pika.BasicProperties(
                        delivery_mode=2  # Make message persistent
                )
            )
            # logging.info(f"Sent frame {frame_obj.f_id} successfully")
        except Exception as e:
            logging.error(f"Failed to send frame {frame_obj.f_id}: {e}")

