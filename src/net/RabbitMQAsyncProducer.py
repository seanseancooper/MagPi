import pika
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] - %(message)s')


class RabbitMQAsyncProducer:
    """RabbitMQ Producer using SelectConnection (async)."""

    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue = None

    def on_channel_open(self, channel):
        """Callback when the channel is opened."""
        logging.info("Channel opened")
        self.channel = channel

        # Declare queue to ensure it exists
        self.channel.queue_declare(queue=self.queue, durable=True, callback=self.on_queue_declared)

    def on_queue_declared(self, _):
        """Callback when the queue is declared."""
        logging.info("Queue declared, ready to publish messages.")

    def on_connection_open(self, connection):
        """Callback when the connection is opened."""
        logging.info("Connection opened")
        self.connection = connection

        # Open channel after connection is established
        self.connection.channel(on_open_callback=self.on_channel_open)

    def on_connection_error(self, _connection, error_message=None):
        """Callback when a connection error occurs."""
        logging.error(f"Connection error: {error_message}")

    def publish_message(self, dictObject):
        """Publish a message (dictionary) to the queue."""
        try:
            message = json.dumps(dictObject)
            self.channel.basic_publish(
                exchange='',
                routing_key=self.queue,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2  # Make message persistent
                )
            )
            logging.info(f"Sent message successfully")
        except Exception as e:
            logging.error(f"Failed to send message: {e}")

    def run(self):
            """Start the asynchronous producer."""
            logging.info("Starting producer...")

            parameters = pika.ConnectionParameters(host='localhost')
            self.connection = pika.SelectConnection(
                parameters=parameters,
                on_open_callback=self.on_connection_open,
                on_open_error_callback=self.on_connection_error
            )

            try:
                logging.info("Starting event loop...")
                self.connection.ioloop.start()
            except KeyboardInterrupt:
                logging.info("Interrupted. Closing connection...")
                self.connection.close()
                self.connection.ioloop.start()


if __name__ == "__main__":
    producer = RabbitMQAsyncProducer()
    producer.run()

