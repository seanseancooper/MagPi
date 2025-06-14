import numpy as np

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from src.sdr.lib import SDRAnalyzer
from src.config import readConfig

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # <- ensure this matches your front-end host

class FlaskSDRStreamer:

    def __init__(self):

        global app
        self.app = app

        self.host = None
        self.port = None
        self.config = {}
        self.configure('sdr.json')
        self.analyzer = SDRAnalyzer()
        self.analyzer.configure('sdr.json')
        self.setup_routes()
        self.debug = False

    def configure(self, config_file):
        readConfig(config_file, self.config)
        host, port = self.config['SERVER_NAME'].split(':')
        self.host = host
        """ the pattern is that capital services add 10 to their ports
            this is a new convention thatI'm playing with; there are other
            ways to do this, but what does it buy me to inject this type of
            business logic here. """
        self.port = int(port) + 10

    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html.j2', analyzer=self.analyzer)

        @socketio.on('extract_signal')
        def handle_extract(data):
            center_freq = self.analyzer.center_freq
            bandwidth = data['bandwidth']
            start_time = data['start_time']
            end_time = data['end_time']

            signal = self.analyzer.extract_signal(center_freq, bandwidth, start_time, end_time)
            emit('signal_extracted', {
                'status': 'done',
                'num_samples': len(signal),
                'sample_rate': self.analyzer.sample_rate
            })

        @socketio.on('read_block')
        def read_block():
            data = self.analyzer.reader.read_block()
            block = self.analyzer.get_magnitudes(data)

            if block is not None:
                emit('block_data', block.astype(np.float32).tobytes())
            else:
                emit('block_data', [])  # or handle error case

        @socketio.on('get_peaks')
        def get_peaks():
            emit('peak_data', self.analyzer.peaks.tolist())

        @socketio.on('meta_data')
        def get_meta_data():

            meta_data = { # fake data!!!
                "id"         : 42,
                "start_time" : "2025-06-01T14:00:00Z",
                "end_time"   : "2025-06-01T14:00:05Z",
                "center_freq": 98.5e6,
                "bandwidth"  : 200e3,
                "modulation" : "FM",
                "snr"        : 27.4,
                "label"      : "Weather Broadcast",
            }

            emit('meta_data', meta_data)

    def run(self):
        socketio.run(self.app, host=self.host, port=self.port, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    app = FlaskSDRStreamer()
    print('FlaskSDRStreamer')
    app.run()
