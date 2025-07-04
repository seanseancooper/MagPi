import numpy as np
from scipy.fftpack import fft

import librosa
from librosa import feature
from python_speech_features import mfcc
from matplotlib import pyplot as plt
from scipy.signal import get_window


class ARXEncoder:

    #
    # Spectral Analysis Features to Extract for Each Signal [scipy.signal, numpy.fft]:
    # Feature                         : Description
    #
    # Mean signal power               : Average strength
    # Variance                        : Signal stability
    # FFT Peak/Dominant Frequency     : Periodic behavior
    # Auto-correlation lag            : Repetitions
    # Coherence with other signals    : Time-dependent similarity
    # Rolling correlation window      : Pairwise time-varying relationships [pandas.rolling().corr()]
    # Mean signal power               : Average strength
    #
    # PCA / UMAP | sklearn, umap-learn
    # Clustering | sklearn.cluster
    # Mutual Information | sklearn.metrics.mutual_info_score
    #


    # Time-Domain Features:
    #     Zero-Crossing Rate (ZCR) – Measures how often the signal changes sign (crosses zero). Useful for distinguishing between voiced and unvoiced sounds.
    #     Root Mean Square (RMS) Energy – Measures the signal’s power, indicating loudness.
    #
    # Frequency-Domain Features:
    #     Mel-Frequency Cepstral Coefficients (MFCCs) – Already included, these model the spectral shape of a signal.
    #     Spectral Centroid – Represents the "center of mass" of the spectrum, giving an idea of brightness.
    #     Spectral Bandwidth – Measures the spread of frequencies in a signal.
    #     Spectral Contrast – Measures the difference between peaks and valleys in the spectrum.
    #     Spectral Roll-off – The frequency below which a given percentage (e.g., 85%) of the total spectral energy is contained.
    #
    # Temporal Features:
    #     Chroma Features – Represent the energy distribution across different pitch classes (useful for music analysis).
    #     Tonnetz (Tonal Centroid Features) – Captures harmonic relationships between notes.

    # librosa deals with arrays of floats, the SDR puts arrays of complex numbers.

    # // ENOB: Effective number of bits
    # DB (_sgnl): decibels
    # SNR: Signal-to-noise ratio
    # THD: Total harmonic distortion
    # THD + N: Total harmonic distortion plus noise
    # SFDR: Spurious free dynamic range
    # SINAD: Signal-to-noise-and-distortion ratio

    # Get RMS value from each frame's magnitude value
    # S, phase = librosa.magphase(librosa.stft(x))
    # rms = librosa.feature.rms(S=S)# Plot the RMS energy

    # audio_fft = np.transpose(audio_fft)
    # audio_power = np.square(np.abs(audio_fft))

    # TEMPOGRAM
    # oenv = librosa.onset.onset_strength(y=x, sr=sr, hop_length=hop_length)
    # times = librosa.times_like(oenv, sr=sr, hop_length=hop_length)
    # tempogram = librosa.feature.tempogram(onset_envelope=oenv, sr=sr,
    #                                       hop_length=hop_length)# Estimate the global tempo for display purposes
    # tempo = librosa.feature.rhythm.tempo(onset_envelope=oenv, sr=sr, hop_length=hop_length)[0]

    # fig, ax = plt.subplots(figsize=(15, 3))
    # img = librosa.display.specshow(tempogram, x_axis='time', y_axis='tempo', hop_length=hop_length, cmap='coolwarm')
    # fig.colorbar(img, ax=ax)

    def __init__(self, audio_data=None, sampling_rate=None):

        self._audio_data = audio_data       # potentially an array, a Signal() or LIST of type
        self._sr = sampling_rate
        self._audio_frequency_features = None
        self._text_attubutes = None

        if audio_data is not None and sampling_rate is not None:
            self._audio_frequency_features = self.compute_audio_frequency_features()

    def get_audio_data(self):
        return self._audio_data

    def set_audio_data(self, audio_data):
        def process_features(_data):
            self._audio_data = _data
            self._sr = self._sr
            yield self.compute_audio_frequency_features()

        if type(audio_data) is np.ndarray:
            process_features(audio_data)

        if type(audio_data) is list:
            self._audio_frequency_features = []
            [self._audio_frequency_features.append(process_features(_data)) for _data in audio_data]

    def get_sampling_rate(self):
        """Get the sampling rate."""
        return self._sr

    def get_audio_frequency_features(self):
        """Get the computed frequency features."""
        return self._audio_frequency_features

    def compute_audio_frequency_features(self):
        """Compute frequency features for the given audio data."""
        return self.extract_audio_features(self._audio_data, self._sr)

    @staticmethod
    def extract_base_features():

        # extract class features
        # geohash the lat, lon
        # Use 'text_attributes' where needed, add to categorical features and geohash the lat, lon

        return {
            "encoded": 0,
        }

    @staticmethod
    def extract_text_attribute_features(text_attributes):

        # extract the categorical features from text attributes geohash the lat, lon
        # Use 'text_attributes' where needed, add to categorical features and geohash the lat, lon

        encoder =  TextEncoder(text_attributes=text_attributes)
        return {
            "encoded": encoder.encoded,
        }

    @staticmethod
    def extract_audio_features(audio_data, sampling_rate):
        if len(audio_data) < 2:
            return {}

        zcr = float(np.mean(librosa.feature.zero_crossing_rate(audio_data)))
        centroid = float(np.mean(librosa.feature.spectral_centroid(y=audio_data, sr=sampling_rate)))
        bandwidth = float(np.mean(librosa.feature.spectral_bandwidth(y=audio_data, sr=sampling_rate)))
        flatness = float(np.mean(librosa.feature.spectral_flatness(y=audio_data)))
        contrast = float(np.mean(librosa.feature.spectral_contrast(y=audio_data, sr=sampling_rate)))
        rolloff = float(np.mean(librosa.feature.spectral_rolloff(y=audio_data, sr=sampling_rate)))
        tempo, _ = librosa.beat.beat_track(y=audio_data, sr=sampling_rate)
        mfccs = librosa.feature.mfcc(y=audio_data, sr=sampling_rate, n_mfcc=13).mean(axis=1).tolist()
        chroma = float(np.mean(librosa.feature.chroma_stft(y=audio_data, sr=sampling_rate)))

        return {
            "zero_crossing_rate": zcr,
            "spectral_centroid": centroid,
            "spectral_bandwidth": bandwidth,
            "spectral_flatness": flatness,
            "spectral_contrast": contrast,
            "spectral_rolloff": rolloff,
            "tempo": float(tempo),
            "mfcc": mfccs,
            "chroma": chroma
        }

    @staticmethod
    def frame_audio(audio, FFT_size=2048, hop_size=10, sr=44100):
        # hop_size in ms

        audio = np.pad(audio, int(FFT_size / 2), mode='reflect')
        frame_len = np.round(sr * hop_size / 1000).astype(int)
        frame_num = int((len(audio) - FFT_size) / frame_len) + 1
        frames = []  # np.zeros((frame_num,FFT_size))

        for n in range(frame_num):
            frame_len_n = n * frame_len
            plus_FFT_size = n * frame_len + FFT_size

            # frames[n] = audio[frame_len_n:plus_FFT_size]
            # print("frame_len:", frame_len)
            # print("frame_len_n:", frame_len_n)
            # print("plus_FFT_size:", plus_FFT_size)
            # print("result:", audio[frame_len_n:plus_FFT_size].shape)

            # frames[n] = audio[frame_len_n:plus_FFT_size]
            frames.append(audio[frame_len_n:plus_FFT_size])

        framed_audio = np.array(frames)

        return framed_audio

    def save_me(self, FFT_size=2048, hop_size=10, sr=44100):

        audio_data = self.get_audio_data()
        audio_framed = self.frame_audio(audio_data, FFT_size=FFT_size, hop_size=hop_size, sr=sr)

        # this controls the size and type of window used to
        # create the fft bins
        window = get_window("hann", FFT_size, fftbins=True)

        # plt.figure(figsize=(15,4))
        # plt.plot(window)
        # plt.grid(True)

        audio_win = audio_framed * window

        print("Framed audio shape: {0}".format(audio_framed.shape))
        print("First frame:", audio_framed[1])
        print("Last frame:", audio_framed[-1])
        print("audio_win.shape",audio_win.shape)

        plt.figure(figsize=(20,6))
        # plt.subplot(2, 1, 1)
        plt.plot(audio_framed)
        plt.title('Original Frame')
        plt.grid(True)

        # plt.subplot(2, 1, 2)
        plt.plot(audio_win)
        plt.title('Frame After Windowing')
        plt.grid(True)

        audio_winT = np.transpose(audio_win)
        print("audio_winT.shape", audio_winT.shape)

        audio_fft = np.empty((int(1 + FFT_size // 2), audio_winT.shape[1]), dtype=np.complex64, order='F')

        for n in range(audio_fft.shape[1]):
            audio_fft[:, n] = fft.fft(audio_winT[:, n], axis=0)[:audio_fft.shape[0]]

        audio_fft = np.transpose(audio_fft)
        audio_power = np.square(np.abs(audio_fft))
        print("audio_power.shape", audio_power.shape)

class TextEncoder:

    def __init__(self, text_attributes=None):
        self._text_attributes = text_attributes
        self.encoded = None
        if self._text_attributes is not None:
            def encode():



                return self.encoded

            encode()
