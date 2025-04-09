import uuid
from datetime import datetime
import hashlib
import numpy as np
import geohash


class SignalPoint(object):
    """
    Base class to handle spatio-temporal properties and frequency feature extraction of a Signal.
    """
    def __init__(self, lon, lat, sgnl):
        self._created = datetime.now()
        self._id = uuid.uuid4()
        self._lon = lon
        self._lat = lat
        self._sgnl = sgnl               # a discrete value
        self._frequency_features = None

    def getId(self):
        return self._id

    def getLatLon(self):
        return self._lat, self._lon

    def getSgnl(self):
        return self._sgnl

    def generate_signal_hash(self, worker_id):
        data = f"{worker_id}-{self._lon}-{self._lat}-{self._sgnl}".encode()
        return hashlib.sha256(data).hexdigest()

    def get_geohash(self, precision=7):
        return geohash.encode(self._lat, self._lon, precision=precision)

    def normalize_signal(self, sgnl):
        return [(sgnl + 100) / 100.0]  # Normalizing from [-100, 0] → [0, 1]

    def compute_fft_features(self, signal_values, sampling_rate=1):

        # Since sgnl is a single value at a point in time, we need to collect multiple signals over
        # a time window (e.g., the last 100 signal points) and analyze their frequency spectrum.
        # Fast Fourier Transform (FFT)
        #
        # FFT converts a time-series signal into a set of frequency components.
        #  We use it to extract dominant frequencies, spectral power, and energy concentration.

        """
        Compute FFT features from a list of signal values.
        :param signal_values: List of past signal strengths.
        :param sampling_rate: Number of samples per second (adjust as needed).
        :return: Dictionary of frequency domain features.
        """

        from scipy.fftpack import fft

        N = len(signal_values)
        fft_vals = np.abs(fft(signal_values))[:N // 2]  # One-sided FFT
        freqs = np.fft.fftfreq(N, d=1 / sampling_rate)[:N // 2]  # Corresponding frequencies

        # Extract dominant frequency and spectral features
        dominant_freq = freqs[np.argmax(fft_vals)]
        spectral_entropy = -np.sum((fft_vals / np.sum(fft_vals)) * np.log2(fft_vals / np.sum(fft_vals)))

        return {
            "dominant_freq": dominant_freq,
            "spectral_entropy": spectral_entropy,
            "fft_magnitude": fft_vals.tolist()
        }
