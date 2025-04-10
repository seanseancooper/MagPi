import pika
import logging

logger_root = logging.getLogger('root')
net_logger = logging.getLogger('net_logger')
speech_logger = logging.getLogger('speech_logger')

class RabbitMQProducer:

    def __init__(self, queue):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.queue = queue
        self.channel.queue_declare(queue=self.queue, durable=True)

    def publish_message(self, message):
        """Send FrameObjekt data to RabbitMQ."""
        try:
            self.channel.basic_publish(
                exchange='',
                routing_key=self.queue,
                body=message,
                properties=pika.BasicProperties(
                        delivery_mode=2  # Make message persistent
                )
            )
            net_logger.info(f"Sent message successfully")
        except Exception as e:
            net_logger.error(f"Failed to send message: {e}")
