import pika
import logging

logger_root = logging.getLogger('root')
net_logger = logging.getLogger('net_logger')
speech_logger = logging.getLogger('speech_logger')


class RabbitMQAsyncProducer:
    """RabbitMQ Producer using SelectConnection (async)."""
    
    def __init__(self, queue):
        self.connection = None
        self.channel = None
        self.queue = queue

    def on_channel_open(self, channel):
        """Callback when the channel is opened."""
        net_logger.info("Channel opened")
        self.channel = channel

        # Declare queue to ensure it exists
        self.channel.queue_declare(queue=self.queue, durable=True, callback=self.on_queue_declared)

    def on_queue_declared(self, _):
        """Callback when the queue is declared."""
        net_logger.info("Queue declared, ready to publish messages.")

    def on_connection_open(self, connection):
        """Callback when the connection is opened."""
        net_logger.info("Connection opened")
        self.connection = connection

        # Open channel after connection is established
        self.connection.channel(on_open_callback=self.on_channel_open)

    def on_connection_error(self, _connection, error_message=None):
        """Callback when a connection error occurs."""
        net_logger.error(f"Connection error: {error_message}")

    def publish_message(self, message):
        """Publish a message (dictionary) to the queue."""
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

    def run(self):
            """Start the asynchronous producer."""
            net_logger.info("Starting producer...")

            parameters = pika.ConnectionParameters(host='localhost')
            self.connection = pika.SelectConnection(
                parameters=parameters,
                on_open_callback=self.on_connection_open,
                on_open_error_callback=self.on_connection_error
            )

            try:
                net_logger.info("Starting event loop...")
                self.connection.ioloop.start()
            except KeyboardInterrupt:
                net_logger.info("Interrupted. Closing connection...")
                self.connection.close()
                self.connection.ioloop.start()


if __name__ == "__main__":
    producer = RabbitMQAsyncProducer()
    producer.run()

