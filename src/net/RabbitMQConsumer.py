# Version: 1.1.0
# Description: RabbitMQ consumer for processing FrameObjekt instances.
# Uses threading for concurrent message handling.
# Message acknowledgment ensures reliable processing.
# Logging added for better monitoring and debugging.

import pika
import json
import numpy as np
from src.cam.Showxating.lib.FrameObjekt import FrameObjekt
from src.cam.Showxating.lib.FrameObjektEncoder import ObjektEncoder
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] - %(message)s')


def dict_to_frameobjekt(data):
    """Convert dictionary back to FrameObjekt."""
    frame_obj = FrameObjekt.create(data['f_id'])
    frame_obj.timestamp = datetime.fromisoformat(data['timestamp'])
    frame_obj.tag = data['tag']

    # frame_obj.contours = np.array(data['contours']) if data['contours'] is not None else None
    # frame_obj.hierarchy = np.array(data['hierarchy']) if data['hierarchy'] is not None else None
    # frame_obj.prev_tag = data['prev_tag']
    # frame_obj.contour_id = data['contour_id']
    frame_obj.curr_dist = data['curr_dist']
    # frame_obj.distances = np.array(data['distances'])
    frame_obj.fd = data['fd']
    frame_obj.fd_mean = data['fd_mean']
    # frame_obj.delta_range = data['delta_range']
    frame_obj.hist_delta = data['hist_delta']
    # frame_obj.f_hist = data['f_hist']
    frame_obj.w_hist = data['w_hist']
    frame_obj.rect = tuple(data['rect']) if data['rect'] else None
    frame_obj.avg_loc = np.array(data['avg_loc'])
    frame_obj.dist_mean = data['dist_mean']
    # frame_obj.wall = np.array(data['wall']) if data['wall'] is not None else None
    frame_obj.close = data['close']
    frame_obj.inside_rect = data['inside_rect']
    frame_obj.hist_pass = data['hist_pass']
    frame_obj.wall_pass = data['wall_pass']
    return frame_obj


def callback(ch, method, properties, body):
    """Callback function for RabbitMQ messages."""
    try:
        data = json.loads(body)
        frame_obj = dict_to_frameobjekt(data)

        # Start encoder thread to process frame
        encoder = ObjektEncoder(frame_obj)
        encoder.start()

        # Acknowledge message after processing starts
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logging.info(f"Acknowledged frame {frame_obj.f_id}")

    except Exception as e:
        logging.error(f"Failed to consume message: {e}")


def main():
    """Main consumer function."""
    logging.info("Starting consumer...")

    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='frame_queue', durable=True)

        channel.basic_consume(queue='frame_queue', on_message_callback=callback)

        logging.info("Waiting for messages. To exit press CTRL+C")
        channel.start_consuming()

    except Exception as e:
        logging.critical(f"Consumer failed: {e}")


if __name__ == "__main__":
    main()
