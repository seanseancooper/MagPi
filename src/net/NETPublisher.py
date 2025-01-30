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

