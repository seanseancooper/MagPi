
import asyncio
import threading
from flask import Flask, Blueprint, jsonify, render_template
from flask_cors import CORS
import numpy as np
from flask_socketio import SocketIO, emit
from src.net.FlaskRESTServer import RESTServer
from src.sdr.lib import SDRAnalyzer
from src.lib.Scanner import Scanner
from src.config import readConfig

import logging

socketio = SocketIO()

class SDRController(threading.Thread):

    def __init__(self):
        super().__init__()
        self.config = {}
        self.debug = False

        self.scanner = Scanner()
        # self.scanner.configure('sdr.json')
        self.analyzer = SDRAnalyzer()
        self.configure()


    def configure(self):
        readConfig('sdr.json', self.config)
        # self.scanner.config = self.config
        self.scanner.configure('sdr.json')
        self.analyzer.config = self.config

    def create_app(self):
        """Create Flask application."""

        app = Flask('sdr',
                    instance_relative_config=True,
                    subdomain_matching=True)

        CORS(app)
        # socketio.init_app(app)

        speech_logger = logging.getLogger('speech_logger')

        with app.app_context():
            if __name__ == '__main__':

                app.config['CORS_HEADERS'] = 'Content-Type'
                app.config['SERVER_NAME'] = self.scanner.config['SERVER_NAME']
                app.config['DEBUG'] = self.scanner.config['DEBUG']

                @app.route('/', methods=['GET'])
                def index():
                    return render_template('sdr.html.j2', analyzer=self.analyzer)

                @app.route('/scan', methods=['GET'])
                def sdr_scan():
                    return jsonify(self.scanner.get_parsed_signals())

                @app.route('/scan/<ident>', methods=['GET'])
                def sdr_scan_ident(ident):
                    worker = self.scanner.module_tracker.get_worker(ident)
                    if worker:
                        return jsonify(worker.get())
                    return "", 404

                @app.route('/tracked', methods=['GET', 'POST'])
                def sdr_tracked():
                    return jsonify(self.scanner.get_tracked_signals())

                @app.route('/ghosts', methods=['GET', 'POST'])
                def sdr_ghosts():
                    return jsonify(self.scanner.get_ghost_signals())

                @app.route('/add/<ident>', methods=['POST'])
                def add(ident):
                    if self.scanner.module_tracker.get_worker(ident).add(ident):
                        if self.scanner.config['SPEECH_ENABLED']:
                            speech_logger.info(f'added')
                        return "OK", 200
                    return "", 404

                @app.route('/mute/<ident>', methods=['POST'])
                def mute(ident):
                    return str(self.scanner.module_tracker.get_worker(ident).mute()), 200

                @app.route('/remove/<ident>', methods=['POST'])
                def remove(ident):
                    if self.scanner.module_tracker.get_worker(ident).remove(ident):
                        if self.scanner.config['SPEECH_ENABLED']:
                            speech_logger.info(f'removed')
                        return "OK", 200
                    return "", 404

                @app.route('/config', methods=['GET'])
                def sdr_config():
                    return jsonify(self.scanner.config)

                #  TODO: let other apps emit stats as well
                @app.route('/stats', methods=['GET'])
                def sdr_stats():
                    return jsonify(self.scanner.stats)

                @app.route('/stop', methods=['POST'])
                def sdr_stop():
                    return self.scanner.stop()

                @socketio.on('extract_signal')
                def handle_extract(data):
                    center_freq = self.analyzer.center_freq
                    bandwidth = data['bandwidth']
                    start_time = data['start_time']
                    end_time = data['end_time']

                    signal = self.analyzer.extract_signal(center_freq, bandwidth, start_time, end_time)
                    emit('signal_extracted', {
                        'status'     : 'done',
                        'num_samples': len(signal),
                        'sample_rate': self.analyzer.sample_rate
                    })

                @socketio.on('read_block')
                def read_block():
                    data = self.scanner.module_retriever.iq_queue.get()
                    # data = self.scanner.module_retriever.block.copy()
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

                    meta_data = {  # fake data!!!
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

            return app

    def run(self) -> None:
        try:
            import atexit

            def stop():
                self.scanner.stop()

            atexit.register(stop)
            app = self.create_app()

            host, port = self.scanner.config['SERVER_NAME'].split(':')

            t = threading.Thread(target=self.scanner.run)
            t.start() # self.scanner.run()

            socketio.init_app(app)
            socketio.run(app, host=host, port=int(port), debug=True)
            # RESTServer(self.create_app()).run()

        except KeyboardInterrupt:
            pass

if __name__ == '__main__':
    SDRController().run()