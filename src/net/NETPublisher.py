# Read & Control a remote instance; process event/signal data from it.
#     > PHASE 1: control a remote MagPi instance running on networked hardware.
#           > MANDATORY: RESOLUTION ON REMOTE INSTANCES, SUBDOMAINS AND PORT CONFLICTS.
#               -- Finding remote instance on a private network
#           > MANDATORY: DOCKER IMAGE AND INSTALLATION ON REMOTE HARDWARE FOR DEV/TEST.

#           > this needs a UI, but don't build a new one (make a NET ViewContainer panel).
#               > NET panel shows (a table of local and connected hosts by hostname/ip address + mac
#               > NET panel has(start, stop, restart buttons) controls connected hosts modules
#                   > start, stop & restart module methods refactored to consistent method on ViewController.
#                   > start, stop & restart module methods access control.
#                   > other ways for user interaction besides module UIs???

#           > is there a way to connect a '0W' to a laptop w/o a network router?
#           > location of a remote host: NEW symbology in the existing MAP module
#           > 'Swagger' integration for hosts?

# PHASE 2

# Finding a remote instance on a public network:
#         what data can be passed, and how?
#         > data sent via control_port differentiated from module REST data.
#         > streamed?
#         > format? binary, text, JSON???
#         when is data passed? incrementally, immediately or in batches? scheduled?
#         differentiating 'discovered' connected hosts. protocol for ident, capabilities, etc.
#       'challenge'/'response' protocol.
#           -- ping port [8080] and look for headers and correct response on a 'control_port'
#

#     > Galatea: read and interpret the Galatea sensor group
#           > (3DOF, temperature, see 'galatea_hdwe_ex')
#           > need configurable widget set for data (ability to visualize realtime data, control subsystems)
#               > pull code from 'sensor' projects ('galatea_hdwe_ex')
#               > special UI widgets for sensors, visualization?

# ....3
#     > BOX: remote install & control 'BOX' hardware (perhaps use Ansible?)
#           > GIVEN DEPS THIS POSSIBLE WITH ANSIBLE, OR K8S/DOCKER?

# publish/subscribe to internal module events:

#   find these codepoints in each module
#     ARX: audio signal detected, labels
#     CAM: image capture, motion detected, labels.
#     GPS: location updated (HARWARE).
#     MAP: None
#     MOT: motion detected, labels?
#     SDR: signal detected, lost.
#     TRX: signal detected.
#     WIFI: signal detected, lost. test passed, failed.
#
#          when trilaterating a signal, have the ability
#          to communicate with the remote instance so as
#          to receive accurate and timely signalpoint
#          updates for a given signal.


# SECURITY: ENCRYPT DATA SENT ACROSS NETWORK.
# authentication: password, token, mac address
# authorization: users, groups, modules

# see "securing flask blueprints..."
#
#
#
#
#
#

import queue
import threading
import time
from PIL import Image
import io
import base64


# Producer function
def producer(q, image_path):
    try:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
        q.put(base64.b64encode(image_data).decode('utf-8'))
        print(f"Produced image: {image_path}")
    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")


# Consumer function
def consumer(q):
    while True:
        image_data_base64 = q.get()
        if image_data_base64 is None:
            break
        image_data = base64.b64decode(image_data_base64)

        try:
            image = Image.open(io.BytesIO(image_data))
            image.save("received_image.jpg")
            print("Consumed and saved image: received_image.jpg")
        except Exception as e:
            print(f"Error processing image: {e}")
        q.task_done()


# Create a queue
q = queue.Queue()

# Create producer and consumer threads
producer_thread = threading.Thread(target=producer, args=(q, "example.jpg"))
consumer_thread = threading.Thread(target=consumer, args=(q,))

# Start the threads
producer_thread.start()
consumer_thread.start()

# Wait for the producer to finish
producer_thread.join()

# Add a sentinel value to signal the consumer to exit
q.put(None)

# Wait for the consumer to finish
consumer_thread.join()
q.join()

print("Done!")