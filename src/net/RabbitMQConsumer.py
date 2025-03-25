# Version: 1.1.0
# Description: RabbitMQ consumer for processing FrameObjekt instances.
# Uses threading for concurrent message handling.
# Message acknowledgment ensures reliable processing.
# Logging added for better monitoring and debugging.

import pika
import json
from src.net.lib.net_utils import dict_to_frameobjekt
from src.cam.Showxating.lib.FrameObjektEncoder import FrameObjektEncoder
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] - %(message)s')


class RabbitMQConsumer:

    """RabbitMQ Consumer using BlockingConnection. """
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='frame_queue', durable=True)

    def on_message(self, method, properties, body):

        """Callback function for RabbitMQ messages."""
        try:
            data = json.loads(body)
            frame_obj = dict_to_frameobjekt(data)

            # Start encoder thread to process frame
            encoder = FrameObjektEncoder(frame_obj)
            encoder.start()

            # Acknowledge message after processing starts
            self.channel.basic_ack(delivery_tag=method.delivery_tag)
            logging.info(f"Acknowledged frame {frame_obj.f_id}")

        except Exception as e:
            logging.error(f"Failed to consume message: {e}")


    def run(self):
        """Main consumer function."""
        logging.info("Starting consumer...")

        try:
            self.channel.basic_consume(queue='frame_queue', on_message_callback=self.on_message)

            logging.info("Waiting for messages. To exit press CTRL+C")
            self.channel.start_consuming()

        except Exception as e:
            logging.critical(f"Consumer failed: {e}")


if __name__ == "__main__":
    consumer = RabbitMQConsumer()
    consumer.run()
