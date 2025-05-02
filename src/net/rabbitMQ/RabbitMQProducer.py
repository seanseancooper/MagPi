import pika
import logging
from src.config import readConfig

logger_root = logging.getLogger('root')
net_logger = logging.getLogger('net_logger')

class RabbitMQProducer:

    def __init__(self, queue):

        self.config = {}
        readConfig('net.json', self.config)

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(self.config['RMQ_HOST']))
        self.channel = self.connection.channel()
        self.queue = queue
        self.channel.queue_declare(queue=self.queue, durable=True)

    def publish_message(self, message):
        """Send message to RabbitMQ."""
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
            print(f"Failed to send message: {e}")
