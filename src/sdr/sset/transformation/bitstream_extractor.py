#  Copyright (c) 2025 Sean D. Cooper
#
#  This source code is licensed under the MIT license found in the LICENSE file in the root directory of this source tree.
#

from matplotlib import pyplot as plt
from scipy.signal import hilbert, chirp
import numpy as np


class BitStreamExtractor:
    """ Taking an AM/FM/PSK signal and extract the baseband signal. """
    # bitstream_extractor.py: Layered decoding of known protocols.
    # Demodulation: Taking an AM/FM/PSK signal and extracting the baseband data.
    # | Shape in PSD                          | Likely Modulation                                                |
    # | ------------------------------------- | ---------------------------------------------------------------- |
    # | Sharp narrow peak                     | **CW (continuous wave)**, **narrowband FM**, unmodulated carrier |
    # | Broader peak with flat top            | **AM**, **DSB-SC** (Double Sideband Suppressed Carrier)          |
    # | Symmetric sidebands                   | **AM**, **QAM**, **PSK**                                         |
    # | Wide spread spectrum                  | **FHSS**, **DSSS**, **OFDM**                                     |
    # | Irregular/hopping structure           | **Frequency hopping**                                            |
    # | Multiple equidistant peaks            | **FSK** (Frequency Shift Keying)                                 |
    # | Constant width, varying height        | Possibly **FSK** or **burst signals**                            |
    # | Peaks that fade or repeat in patterns | **TDMA**, **bursty data**                                        |

    def __init__(self, signal, proc_options, sr=48000):
        self.signal = signal
        self.sr = sr
        self.proc_options = {}
        self.extracted = None

    def config(self):
        pass

    def get_signal_type(self):
        signal_type = None
        # what characteristics define the modulation type?
        return signal_type

    def extract_AM_signal(self, am_signal, options=None):
        if options is None:
            options = {}

        N = options.get('N', None)
        axis = options.get('axis', -1)

        analytic_signal = hilbert(am_signal, N=N, axis=axis)
        amplitude_envelope = np.abs(analytic_signal)

        return amplitude_envelope

    def extract_FM_signal(self, fm_signal, options=None):
        if options is None:
            options = {}

        analytic = hilbert(fm_signal)
        instantaneous_phase = np.unwrap(np.angle(analytic))
        instantaneous_frequency = np.diff(instantaneous_phase) * (self.sr / (2.0 * np.pi))

        return instantaneous_frequency

    def extract_ASK_signal(self, ask_signal, options=None):
        if options is None:
            options = {}

        analytic_signal = hilbert(ask_signal)
        amplitude_envelope = np.abs(analytic_signal)

        return amplitude_envelope

    def extract_FSK_signal(self, fsk_signal, options=None):
        if options is None:
            options = {}

        analytic = hilbert(fsk_signal)
        instantaneous_phase = np.unwrap(np.angle(analytic))
        instantaneous_frequency = np.diff(instantaneous_phase) * (self.sr / (2.0 * np.pi))

        return instantaneous_frequency

    def extract_PSK_signal(self, psk_signal, options=None):
        if options is None:
            options = {}

        analytic = hilbert(psk_signal)
        instantaneous_phase = np.unwrap(np.angle(analytic))

        return instantaneous_phase

    def extract_QAM_signal(self, qam_signal, options=None):
        if options is None:
            options = {}

        analytic = hilbert(qam_signal)
        amplitude = np.abs(analytic)
        phase = np.unwrap(np.angle(analytic))

        return amplitude, phase

    def process_signal(self, signal, type, proc_options):

        type = type or self.get_signal_type()
        ext_signal = None
        extract_options = proc_options['proc_options']

        if type:  # modulation types

            MODULATION_TYPES = {
                "AM" : self.extract_AM_signal,
                "FM" : self.extract_FM_signal,
                "ASK": self.extract_ASK_signal,
                "FSK": self.extract_FSK_signal,
                "PSK": self.extract_PSK_signal,
                "QAM": self.extract_QAM_signal,
            }

            ext_method = MODULATION_TYPES[type]
            ext_signal = ext_method(signal, extract_options)

        return ext_signal
