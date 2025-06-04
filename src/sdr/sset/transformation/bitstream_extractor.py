#  Copyright (c) 2025 Sean D. Cooper
#
#  This source code is licensed under the MIT license found in the LICENSE file in the root directory of this source tree.
#

from matplotlib import pyplot as plt
from scipy.signal import hilbert, chirp


class BitStreamExtractor:
    """ Taking an AM/FM/PSK signal and extract the baseband signal. """
    # bitstream_extractor.py: Layered decoding of known protocols.
    # Demodulation: Taking an AM/FM/PSK signal and extracting the baseband data.

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

        # Broadcast transmissions: still widely used for broadcasting on the long, medium and short wave bands.
        # Air band radio: VHF transmissions for many airborne applications still use AM.
        # Single sideband: Amplitude modulation in the form of single sideband is still used for HF radio links.
        # Quadrature amplitude modulation:  Wi-Fi to cellular telecommunications formed by having two carriers 90° out of phase.

        # One of the aspects associated with amplitude modulation is sidebands are generated.
        # These govern the bandwidth of the signal.

        # It is found that if a carrier is modulated with a single tone, e.g. 1 kHz, then two sidebands will appear,
        # one either side of the main carrier spaced by 1 kHz away from it.

        # Similarly if modulation with a variety of frequencies, e.g. speech or music is used, then the sidebands
        # will spread out either side of the carrier, extended out by an amount equal to the top frequencies used

        # duration, fs = 1, 400  # 1 s signal with sampling frequency of 400 Hz
        # t = np.arange(int(fs * duration)) / fs  # timestamps of samples
        # am_signal = chirp(t, 20.0, t[-1], 100.0)
        # f = 2.0
        # am_signal *= (1.0 + 0.5 * np.sin(f * np.pi * 3.0 * t))

        # The modulation index (%): level of modulation used, and the maximum modulation can be w/o distortion.

        r"""FFT-based computation of the analytic signal.

        The analytic signal is calculated by filtering out the negative frequencies and
        doubling the amplitudes of the positive frequencies in the FFT domain.
        The imaginary part of the result is the hilbert transform of the real-valued input
        signal.

        The transformation is done along the last axis by default.

        Parameters
        ----------
        x : array_like
            Signal data.  Must be real.
        N : int, optional
            Number of Fourier components.  Default: ``x.shape[axis]``
        axis : int, optional
            Axis along which to do the transformation.  Default: -1.

        Returns
        -------
        xa : ndarray
            Analytic signal of `x`, of each 1-D array along `axis`
        """
        N = options.get('N', None)
        axis = options.get('axis', None)

        processed = hilbert(am_signal, N=N, axis=axis)  # what I want
        # amplitude_envelope = np.abs(processed)
        # instantaneous_phase = np.unwrap(np.angle(processed))
        # instantaneous_frequency = np.diff(instantaneous_phase) / (2.0 * np.pi) * sr

        # return extracted AM baseband signal.
        return processed

    def extract_FM_signal(self, fm_signal, options):

        n = fm_signal.size
        timestep = 0.1                  # with sr should be able to calculate this?

        d = options.get('d', None)
        device = options.get('device', None)
        """
        Return the Discrete Fourier Transform sample frequencies.

        The returned float array `f` contains the frequency bin centers in cycles
        per unit of the sample spacing (with zero at the start).  For instance, if
        the sample spacing is in seconds, then the frequency unit is cycles/second.

        Given a window length `n` and a sample spacing `d`::

          f = [0, 1, ...,   n/2-1,     -n/2, ..., -1] / (d*n)   if n is even
          f = [0, 1, ..., (n-1)/2, -(n-1)/2, ..., -1] / (d*n)   if n is odd

        Parameters
        ----------
        n : int
            Window length.
        d : scalar, optional
            Sample spacing (inverse of the sampling rate). Defaults to 1.
        device : str, optional
            The device on which to place the created array. Default: ``None``.
            For Array-API interoperability only, so must be ``"cpu"`` if passed.

            .. versionadded:: 2.0.0

        Returns
        -------
        f : ndarray
            Array of length `n` containing the sample frequencies.

        Examples
        --------
        >>> import numpy as np
        >>> signal = np.array([-2, 8, 6, 4, 1, 0, 3, 5], dtype=float)
        >>> fourier = np.fft.fft(signal)
        >>> n = signal.size
        >>> timestep = 0.1
        >>> freq = np.fft.fftfreq(n, d=timestep)
        >>> freq
        array([ 0.  ,  1.25,  2.5 , ..., -3.75, -2.5 , -1.25])

        """
        NFFT = 1024*4
        # use matplotlib to estimate and plot the PSD
        processed, f = plt.psd(fm_signal, NFFT=NFFT)

        # processed = np.fft.fftfreq(n, d=timestep, device=device)
        return processed

    def extract_ASK_signal(self, ask_signal, options):  # Amplitude Shift Keying (ASK)
        # The common operating mode of Ethernet uses a 4-level amplitude modulation (2 bits per symbol) with 8 ns symbols.


        processed = None
        option = options['option']
        yield processed

    def extract_FSK_signal(self, fsk_signal, options):  # Frequency Shift Keying (FSK)
        processed = None
        option = options['option']
        yield processed

    def extract_PSK_signal(self, psk_signal, options):  # Phase Shift Keying (PSK)
        # The simplest form is Binary PSK, a.k.a. BPSK, two levels of phase.
        # The simplest form is Quadrature Phase Shift Keying (QPSK), two levels of phase.
        processed = None
        option = options['option']
        yield processed

    def extract_QAM_signal(self, psk_signal, options):  # combine ASK and PSK? Quadrature Amplitude Modulation (QAM)
        # 16 QAM
        # 32 QAM
        # 64 QAM
        # 256 QAM

        processed = None
        option = options['option']
        yield processed

    def process_signal(self, signal, type, proc_options):

        type = type or self.get_signal_type()
        ext_signal = None
        extract_options = proc_options['proc_options']

        if type:  # modulation types

            MODULATION_TYPES = {
                "AM" : self.extract_AM_signal,
                "FM" : self.extract_FM_signal,
                "ASK": self.extract_ASK_signal,
                "FSK": self.extract_ASK_signal,
                "PSK": self.extract_PSK_signal,
            }

            ext_method = MODULATION_TYPES[type]
            ext_signal = ext_method(signal, extract_options)

        return ext_signal



