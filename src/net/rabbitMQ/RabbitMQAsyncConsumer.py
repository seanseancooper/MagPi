import pika
import logging
from src.config import readConfig

logger_root = logging.getLogger('root')
net_logger = logging.getLogger('net_logger')


class RabbitMQAsyncConsumer:
    """RabbitMQ Consumer using SelectConnection (async)."""

    def __init__(self, queue):
        self.connection = None
        self.channel = None
        self.queue = queue
        self.data = None

    def on_channel_open(self, channel):
        """Callback when the channel is successfully opened."""
        net_logger.info("Channel opened")
        self.channel = channel
        # Declare queue to ensure it exists
        channel.queue_declare(queue=self.queue, durable=True, callback=self.on_queue_declared)

    def on_queue_declared(self, _):
        """Callback after queue declaration."""
        net_logger.info("Queue declared, starting consumption...")
        self.channel.basic_consume(queue=self.queue, on_message_callback=self.on_message)

    def on_connection_open(self, connection):
        """Callback when the connection is successfully opened."""
        net_logger.info("Connection opened")
        self.connection = connection
        self.connection.channel(on_open_callback=self.on_channel_open)

    def on_connection_error(self, _connection, error_message=None):
        """Callback when a connection error occurs."""
        net_logger.error(f"Connection error: {error_message}")

    def on_message(self, channel, method, properties, body):
        """Callback function for processing messages."""
        try:
            if body:
                self.data = str(body.decode())
                net_logger.debug(self.data)
                self.channel.basic_ack(delivery_tag=method.delivery_tag)
                return self.data

        except Exception as e:
            net_logger.error(f"[{__name__} Failed to process body: {e}")

    def run(self):
        """Start the asynchronous consumer."""
        net_logger.info("Starting consumer...")

        config = {}
        readConfig('net.json', config)
        parameters = pika.ConnectionParameters(host=config['RMQ_HOST'])

        try:
            self.connection = pika.SelectConnection(
                    parameters=parameters,
                    on_open_callback=self.on_connection_open,
                    on_open_error_callback=self.on_connection_error
            )
            net_logger.info("Starting event loop...")
            self.connection.ioloop.start()
        except KeyboardInterrupt:
            net_logger.info("Interrupted. Closing connection...")
            self.connection.close()

if __name__ == "__main__":
    queue_name = 'some_queue'
    consumer = RabbitMQAsyncConsumer(queue_name)
    consumer.run()
