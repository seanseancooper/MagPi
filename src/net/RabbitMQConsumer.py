import pika
import logging

logger_root = logging.getLogger('root')
net_logger = logging.getLogger('net_logger')
speech_logger = logging.getLogger('speech_logger')


class RabbitMQConsumer:
    """RabbitMQ Consumer using BlockingConnection. """
    
    def __init__(self, queue):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.queue = queue
        self.channel.queue_declare(queue=self.queue, durable=True)
        self.data = None

    def on_message(self, method, properties, body):

        """Callback function for RabbitMQ messages."""
        try:
            self.data = str(body.decode)
            self.channel.basic_ack(delivery_tag=method.delivery_tag)
            return self.data

        except Exception as e:
            net_logger.error(f"Failed to consume message: {e}")

    def run(self):
        """Main consumer function."""
        net_logger.info("Starting consumer...")

        try:
            self.channel.basic_consume(queue=self.queue, on_message_callback=self.on_message)

            net_logger.info("Waiting for messages. To exit press CTRL+C")
            self.channel.start_consuming()

        except Exception as e:
            net_logger.critical(f"Consumer failed: {e}")


if __name__ == "__main__":
    consumer = RabbitMQConsumer('test_queue')
    consumer.run()
