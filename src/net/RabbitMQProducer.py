# Version: 1.1.0
# Description: RabbitMQ producer for sending FrameObjekt instances as JSON messages.
# Uses pika for RabbitMQ communication.
# Message persistence enabled for reliability.
# Logging added for better monitoring and debugging.

import pika
import json
import numpy as np
from src.cam.Showxating.lib import FrameObjekt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] - %(message)s')


def frameobjekt_to_dict(frame_obj):
    """Convert FrameObjekt to a serializable dictionary."""
    return {
        'f_id': frame_obj.f_id,
        'timestamp': frame_obj.timestamp.isoformat(),
        'tag': frame_obj.tag,
        'isNew': frame_obj.isNew,
        'skip': frame_obj.skip,
        'contours': frame_obj.contours.tolist() if frame_obj.contours is not None else None,
        'hierarchy': frame_obj.hierarchy.tolist() if frame_obj.hierarchy is not None else None,
        'prev_tag': frame_obj.prev_tag,
        'contour_id': frame_obj.contour_id,
        'curr_dist': frame_obj.curr_dist,
        'distances': frame_obj.distances.tolist(),
        'fd': frame_obj.fd,
        'fd_mean': frame_obj.fd_mean,
        'delta_range': frame_obj.delta_range,
        'hist_delta': frame_obj.hist_delta,
        'rect': frame_obj.rect,
        'avg_loc': frame_obj.avg_loc.tolist(),
        'dist_mean': frame_obj.dist_mean,
        'wall': frame_obj.wall.tolist() if frame_obj.wall is not None else None,
        'close': frame_obj.close,
        'inside_rect': frame_obj.inside_rect,
        'hist_pass': frame_obj.hist_pass,
        'wall_pass': frame_obj.wall_pass
    }


def send_frameobjekt(channel, frame_obj):
    """Send FrameObjekt data to RabbitMQ."""
    try:
        message = json.dumps(frameobjekt_to_dict(frame_obj))
        channel.basic_publish(
            exchange='',
            routing_key='frame_queue',
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
        )
        logging.info(f"Sent frame {frame_obj.f_id} successfully")
    except Exception as e:
        logging.error(f"Failed to send frame {frame_obj.f_id}: {e}")


def main():
    """Main producer function."""
    logging.info("Starting producer...")

    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='frame_queue', durable=True)

        # Create and populate a FrameObjekt instance
        frame_obj = FrameObjekt.create(f_id=1)
        frame_obj.tag = FrameObjekt.create_tag(f_id=1)
        frame_obj.avg_loc = np.array([100, 200])
        frame_obj.rect = (10, 20, 30, 40)
        frame_obj.dist_mean = 15.5
        frame_obj.distances = np.array([[1.0, 2.0], [3.0, 4.0]])
        frame_obj.fd = 5.5
        frame_obj.fd_mean = 4.4
        frame_obj.hist_delta = 0.75
        frame_obj.close = True
        frame_obj.inside_rect = False
        frame_obj.hist_pass = True
        frame_obj.wall_pass = False

        send_frameobjekt(channel, frame_obj)

        connection.close()
        logging.info("Connection closed")

    except Exception as e:
        logging.critical(f"Producer failed: {e}")


if __name__ == "__main__":
    main()
