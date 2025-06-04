#  Copyright (c) 2025 Sean D. Cooper
#
#  This source code is licensed under the MIT license found in the LICENSE file in the root directory of this source tree.
#
# signal_semiotics_toolkit/core/signal_model.py

import numpy as np
from scipy.signal import get_window
from typing import Optional, Dict, Any, List


class SignalFrame:
    """
    Transposition:
    A SignalFrame captures a representation of the signal as n-dimensional data.
    SignalFrame can be mutated to either the time or frequency domain, returning a new SignalFrame in the apropos
    domain with magnitude & phase.
    """
    def __init__(
        self,
        timestamp: float,
        duration: float,
        carrier_freq: float,
        bandwidth: float,
        data: np.ndarray,
        # why does this not have a sample rate as a top level field
        domain: str = "time",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Represents a segment or 'frame' of an EM signal in either time or frequency domain.

        Parameters:
        - timestamp: Time of capture (seconds since epoch)
        - duration: Duration of the frame in seconds
        - carrier_freq: Central frequency in Hz
        - bandwidth: Signal width in Hz
        - data: Array representing IQ samples, power spectrum, or waveform
        - domain: 'time', 'frequency', or future: 'mixed'
        - metadata: Arbitrary static or dynamic metadata
        """

        self.timestamp = timestamp
        self.duration = duration
        self.carrier_freq = carrier_freq
        self.bandwidth = bandwidth
        self.data = data
        self.domain = domain
        self.metadata = metadata or {}

        self.phase = float
        self.magnitude = np.ndarray
        self.window = None
        self.set_magnitude_phase()  # calculate on init

    def get_timestamp(self) -> float:
        return self.timestamp

    def get_duration(self) -> float:
        # calculate and set this from self.timestamp
        return self.duration

    def get_carrier_freq(self) -> float:
        return self.carrier_freq

    def get_bandwidth(self) -> float:
        return self.bandwidth

    def get_data(self):
        return self.data

    def set_data(self, data: np.ndarray):
        self.data = data
        self.set_magnitude_phase()  # recalculate for new data

    def get_domain(self) -> str:
        return self.domain

    def get_metadata(self) -> Optional[Dict[str, Any]]:
        return self.metadata

    def set_metadata(self, metadata: Optional[Dict[str, Any]]):
        self.metadata = metadata

    def get_metadata_value_by_key(self, meta_key: str):
        return self.metadata[meta_key]

    def set_metadata_value_by_key(self, meta_key: str, meta_val):
        self.metadata[meta_key] = meta_val

    def get_phase(self) -> float:
        m, p = self.set_magnitude_phase()
        return p

    def get_magnitude(self) -> np.ndarray:
        m, _ = self.set_magnitude_phase()
        return m

    def set_magnitude_phase(self) -> (np.ndarray, float):
        data = self.data                # default
        if self.domain == "frequency":  # 'mixed' TBD
            data = np.fft.fft(self.data)
        m = np.abs(data)
        p = np.angle(data)
        return m, p

    def get_window(self) -> object:
        return self.window

    def set_window(self, window, size):
        self.window = get_window(window, size)

    def to_frequency_domain(self):
        if self.domain == "frequency":
            return self
        spectrum = np.fft.fft(self.data)  # data is time-domain
        self.set_magnitude_phase()
        return SignalFrame(
            timestamp=self.timestamp,
            duration=self.duration,
            carrier_freq=self.carrier_freq,
            bandwidth=self.bandwidth,
            data=np.abs(spectrum),
            domain="frequency",
            metadata=self.metadata
        ), (self.magnitude, self.phase)

    def to_time_domain(self):
        if self.domain == "time":
            return self
        waveform = np.fft.ifft(self.data)  # data is frequency-domain
        self.set_magnitude_phase()
        return SignalFrame(
            timestamp=self.timestamp,
            duration=self.duration,
            carrier_freq=self.carrier_freq,
            bandwidth=self.bandwidth,
            data=np.real(waveform),
            domain="time",
            metadata=self.metadata
        ), (self.magnitude, self.phase)

    def __lt__(self, other):
        return self.timestamp < other.timestamp

    def __eq__(self, other):
        return (
                isinstance(other, SignalFrame)
                and self.timestamp == other.timestamp
                and self.carrier_freq == other.carrier_freq
                and self.domain == other.domain
        )



