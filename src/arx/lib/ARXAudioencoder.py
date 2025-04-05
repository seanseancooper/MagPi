import numpy as np


class ARXEncoder():

    def __init__(self, audio_data, sampling_rate):
        self._audio_data = audio_data
        self._frequency_features = None
        self._sampling_rate = sampling_rate
        self._frequency_features = self.compute_audio_frequency_features()

    def get_audio_data(self):
        """
        Accessor method for raw audio data.
        """
        return self._audio_data

    def set_audio_data(self, audio_data):
        """
        Mutator method for raw audio data.
        """
        self._audio_data = audio_data
        self._frequency_features = self.compute_audio_frequency_features()

    def compute_audio_frequency_features(self):

        import librosa
        from librosa import feature

        if len(self._audio_data) < 2:
            return {}

        # AUDIO FREQUENCY FEATURES:
        # // ENOB: Effective number of bits

        # DB (_sgnl): decibels
        # SNR: Signal-to-noise ratio
        # THD: Total harmonic distortion
        # THD + N: Total harmonic distortion plus noise

        # SFDR: Spurious free dynamic range
        # SINAD: Signal-to-noise-and-distortion ratio

        flatness = float(np.mean(feature.spectral_flatness(y=self._audio_data)))                            # Spectral flatness
        contrast = float(np.mean(feature.spectral_contrast(y=self._audio_data, sr=self._sampling_rate)))    # Spectral contrast

        centroid = float(np.mean(feature.spectral_centroid(y=self._audio_data, sr=self._sampling_rate)))    # Spectral centroid
        bandwidth = float(np.mean(feature.spectral_bandwidth(y=self._audio_data, sr=self._sampling_rate)))  # Spectral bandwidth
        rolloff = float(np.mean(feature.spectral_rolloff(y=self._audio_data, sr=self._sampling_rate)))      # Spectral rolloff

        chroma = float(np.mean(feature.chroma_stft(y=self._audio_data, sr=self._sampling_rate)))            # Chroma feature
        tempo, _ = librosa.beat.beat_track(y=self._audio_data, sr=self._sampling_rate)                            # Tempo estimation
        # rhythm
        zcr = float(np.mean(feature.zero_crossing_rate(self._audio_data)))                                  # Zero crossing rate
        mfccs = feature.mfcc(y=self._audio_data, sr=self._sampling_rate, n_mfcc=13).mean(axis=1).tolist()         # MFCC features

        return {
            "spectral_flatness" : flatness,
            "spectral_contrast" : contrast,
            "spectral_centroid" : centroid,
            "spectral_bandwidth": bandwidth,
            "spectral_rolloff"  : rolloff,
            "chroma"            : chroma,
            "tempo"             : float(tempo),
            "zero_crossing_rate": zcr,
            "mfcc"              : mfccs,
        }

    def compute_spectral_frequency_features(self):
        """
        Compute continuous audio-specific frequency features (e.g., MFCC) from raw audio data.
        """
        from python_speech_features import mfcc

        mfcc_features = mfcc(self._audio_data, samplerate=self._sampling_rate, numcep=13)

        return {
            "mfcc"            : mfcc_features.mean(axis=0).tolist(),
            "dominant_freq"   : float(np.argmax(np.abs(np.fft.fft(self._audio_data)))),
            "spectral_entropy": float(
                    -np.sum((np.abs(np.fft.fft(self._audio_data)) / np.sum(np.abs(np.fft.fft(self._audio_data)))) *
                            np.log2(
                                np.abs(np.fft.fft(self._audio_data)) / np.sum(np.abs(np.fft.fft(self._audio_data))))))
        }

    def compute_frequency_featuresv_1(self, signal, sampling_rate=1):
        """
        Compute FFT-based frequency features and MFCCs from signal.
        """

        from librosa import feature

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

    def compute_frequency_features(self, past_signals, sampling_rate=1):
        """
        Compute FFT-based frequency features and MFCCs from past signal strengths.
        Ensures output FFT length is 50 via zero-padding if needed.
        """

        from scipy.fftpack import fft
        from python_speech_features import mfcc

        MIN_LEN = 50

        if len(past_signals) < 2:
            return {"dominant_freq": None, "spectral_entropy": None, "fft_magnitude": [0.0]*MIN_LEN, "mfcc": [0.0]*13}

        signal_values = np.array(past_signals)  # Convert list to numpy array for efficient manipulation
        N = len(signal_values)

        # Pad signal with zeros if less than MIN_LEN
        if N < MIN_LEN:
            signal_values = np.pad(signal_values, (0, MIN_LEN - N), 'constant')
            N = MIN_LEN

        fft_vals = np.abs(fft(signal_values))[:MIN_LEN]  # Always get first 50 values
        freqs = np.fft.fftfreq(N, d=1 / sampling_rate)[:MIN_LEN]

        dominant_freq = freqs[np.argmax(fft_vals)]
        normalized_fft = fft_vals / np.sum(fft_vals) if np.sum(fft_vals) > 0 else np.ones_like(fft_vals) / len(fft_vals)
        spectral_entropy = -np.sum(normalized_fft * np.log2(normalized_fft + 1e-12))  # Spectral entropy computation

        try:
            mfcc_features = mfcc(signal_values.reshape(-1, 1), samplerate=sampling_rate, numcep=13)  # Extract MFCC features
            mfcc_mean = mfcc_features.mean(axis=0).tolist()  # Average MFCC coefficients
        except Exception:
            mfcc_mean = [0.0] * 13  # In case MFCC extraction fails, return default zero values

        return {
            "dominant_freq": float(dominant_freq),
            "spectral_entropy": float(spectral_entropy),
            "fft_magnitude": fft_vals.tolist(),
            "mfcc": mfcc_mean
        }
