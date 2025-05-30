import queue
import threading
from datetime import datetime

from rtlsdr import RtlSdr
from scipy.signal import find_peaks, periodogram
from matplotlib.mlab import psd
import numpy as np

from src.config import readConfig
from src.lib.utils import format_time, generate_uuid

def file_writing_thread(*, q, **blockfile_args):
    """
    Thread function to continuously write audio data from queue to a file.
    Stops when it gets a `None` item.
    """
    with open(**blockfile_args) as f:
        while True:
            data = q.get()
            if data is None:
                break
            f.write(data)

class RTLSDRReceiver(threading.Thread):

    def __init__(self):
        """Initialize the SDR hardware with provided parameters.
        Received energy on a particular frequency may start a recorder, and alert a human
        to listen to the signals if they are intelligible (i.e., COMINT). If the frequency
        is not known, the operators may look for power on primary or sideband frequencies
        using a spectrum analyzer. Information from the spectrum analyzer is then used to
        tune receivers to signals of interest.
        """
        super().__init__()
        self.sdr = None
        self.thread = None
        self.config = {}
        self.data = None
        self.signalpoint = None
        self.parsed_cells = None
        self.nfft_size = 4096
        self.block = None
        self.iqq = queue.Queue()      # Unbounded queue for I/Q data
        self._OUTFILE = None

    def configure(self, config_file):

        readConfig(config_file, self.config)

        self.sdr = RtlSdr()
        self.sdr.sample_rate = self.config['DEFAULT_SAMPLE_RATE']
        self.sdr.center_freq = self.config['DEFAULT_CENTER_FREQ']
        self.sdr.freq_correction = self.config['DEFAULT_FREQ_CORRECTION']
        self.sdr.gain = self.config['DEFAULT_GAIN']

    def get_sample_rate(self):
        return self.sdr.sample_rate

    def get_center_freq(self):
        return self.sdr.center_freq

    def get_freq_correction(self):
        return self.sdr.freq_correction

    def get_gain(self):
        return self.sdr.gain

    def set_gain(self, gain_value):
        self.sdr.gain = gain_value

    def set_block(self, scanned):
        if type(scanned) is list:
            self.block = scanned[0]
        if type(scanned) is np.array:
            self.block = scanned

        self.iqq.put(self.block.copy())

    def get_block(self, scanned):
        self.set_block(scanned)
        return self.block

    def get_psd_for_block(self):
        psd_scan, f = psd(self.block, NFFT=self.nfft_size)
        return psd_scan, f

    def get_peaks(self):
        psd_scan, f = self.get_psd_for_block()

        max = np.max(psd_scan)
        height = max - (.10*max)

        peaks, _ = find_peaks(psd_scan, height=height)
        print(f'max: {max}, height: {height}, peaks: {peaks}')
        return peaks, _

    def get_peak_freq(self, peak):

        psd_scan, f = self.get_psd_for_block()
        return psd_scan[peak]  + self.config['DEFAULT_CENTER_FREQ']

    def get_peak_power(self, peak):
        psd_scan, f = self.get_psd_for_block()
        return psd_scan[peak]

    def get_parsed_cells(self, scanned):

        if not scanned:
            return []

        self.get_block(scanned)

        peaks, _ = self.get_peaks()
        print(peaks)

        self.parsed_cells = []
        for peak in peaks:

            text_attributes = {
                'sample_rate': self.config['DEFAULT_SAMPLE_RATE'],
                'center_freq': self.config['DEFAULT_CENTER_FREQ'],
                'freq_corr'  : self.config['DEFAULT_FREQ_CORRECTION'],
                'gain'       : self.config['DEFAULT_GAIN'],
            }

            cell = {
                'peak_freq'      : self.get_peak_freq(peak),
                "created"        : format_time(datetime.now(), "%Y-%m-%d %H:%M:%S.%f"),
                "id"             : str(generate_uuid()),
                "worker_id"      : '',
                "lon"            : 0.0,
                "lat"            : 0.0,
                "sgnl"           : self.get_peak_power(peak),  # calculate abs magnitude
                "text_attributes": text_attributes,
                "audio_data"     : None,
                'cell_type'      : 'sdr',
                'is_mute'        : False,
                'tracked'        : False,
            }

            self.parsed_cells.append(cell)

        [print(cell) for cell in self.parsed_cells]

        return self.parsed_cells

    def run(self):

        self.thread = threading.Thread(
                target=file_writing_thread,
                kwargs=dict(
                        file=self._OUTFILE,
                        mode='w',
                        q=self.iqq,
                ),
                daemon=False,  # Important: non-daemon to finalize files correctly
        )
        self.thread.start()

    def scan(self):

        def get_data(NFFT):
            if not self.sdr.device_opened:
                self.sdr.open()

            if not self.thread:
                self.run()

            s = self.read_samples(NFFT)  # get rid of initial empty samples
            if s.any():
                return s                 # no contract
            return None

        scanned = get_data(self.nfft_size)

        return [scanned]  # contract is list of T

    def read_samples(self, num_samples=4096):
        """Read samples from the SDR."""
        return self.sdr.read_samples(num_samples)

    def print_device_info(self):
        """Print the length of samples and valid gains for the SDR."""
        print(len(self.read_samples(num_samples=self.nfft_size)))
        print(self.sdr.valid_gains_db)

if __name__ == '__main__':
    sdr_analyzer = RTLSDRReceiver()
    sdr_analyzer.configure('sdr.json')
    sdr_analyzer.set_gain(49.6)

    fft_size=512
    num_rows=500

    sdr_analyzer.print_device_info()

    data = sdr_analyzer.scan()
    print(data)


