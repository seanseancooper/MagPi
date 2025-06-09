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
        self.port = int(port) + 10

    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html.j2')

        @socketio.on('extract_signal')
        def handle_extract(data):
            center_freq = data['center_freq']
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
            block = self.analyzer.generate_spectrogram_row(data)

            if block is not None:
                emit('block_data', block.astype(np.float32).tobytes())
            else:
                emit('block_data', [])  # or handle error case

    def run(self):
        socketio.run(self.app, host=self.host, port=self.port, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    app = FlaskSDRStreamer()
    print('FlaskSDRStreamer')
    app.run()
