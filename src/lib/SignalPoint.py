import uuid
from librosa import feature
import numpy as np
from datetime import datetime

class SignalPoint(object):
    """
    Base class to handle spatio-temporal properties and frequency feature extraction.
    """

    def __init__(self, lon, lat, sgnl):
        self._created = datetime.now()
        self._id = uuid.uuid4()
        self._lon = lon
        self._lat = lat
        self._sgnl = sgnl
        self._frequency_features = None
        self.scanner = None

    def set_scanner(self, scanner):
        """
        Set a Scanner instance.
        """
        self.scanner = scanner

    def getId(self):
        return self._id

    def getLatLon(self):
        return self._lat, self._lon

    def getSgnl(self):
        return self._sgnl


    def compute_frequency_features(self, signal, sampling_rate=1):
        """
        Compute FFT-based frequency features and MFCCs from signal.
        """
        # Calculate FFT
        N = len(signal)
        fft_vals = np.abs(np.fft.fft(signal))[:N // 2]
        freqs = np.fft.fftfreq(N, d=1 / sampling_rate)[:N // 2]

        dominant_freq = freqs[np.argmax(fft_vals)]
        spectral_entropy = -np.sum((fft_vals / np.sum(fft_vals)) * np.log2(fft_vals / np.sum(fft_vals)))

        # Calculate MFCCs
        mfcc_features = feature.mfcc(y=signal, sr=sampling_rate, n_mfcc=13)

        return {
            "dominant_freq"   : float(dominant_freq),
            "spectral_entropy": float(spectral_entropy),
            "fft_magnitude"   : fft_vals.tolist(),
            "mfcc"            : mfcc_features.mean(axis=1).tolist()  # Take mean across frames
        }
