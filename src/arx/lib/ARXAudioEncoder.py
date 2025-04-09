import numpy as np
from scipy.fftpack import fft
from python_speech_features import mfcc
import librosa
from librosa import feature


class ARXEncoder:
    @staticmethod
    def extract_signal_strength_features(past_signals, sampling_rate=1):
        MIN_LEN = 50

        if len(past_signals) < 2:
            return {"dominant_freq": None, "spectral_entropy": None, "fft_magnitude": [0.0]*MIN_LEN, "mfcc": [0.0]*13}

        signal_values = np.array(past_signals)
        N = len(signal_values)

        if N < MIN_LEN:
            signal_values = np.pad(signal_values, (0, MIN_LEN - N), 'constant')
            N = MIN_LEN

        fft_vals_full = np.abs(fft(signal_values))
        fft_vals = fft_vals_full[:N // 2]

        fft_vals_50 = np.zeros(MIN_LEN)
        fft_clip = fft_vals[:MIN_LEN] if len(fft_vals) >= MIN_LEN else fft_vals
        fft_vals_50[:len(fft_clip)] = fft_clip

        freqs = np.fft.fftfreq(N, d=1 / sampling_rate)[:N // 2]
        dominant_freq = freqs[np.argmax(fft_vals)]
        normalized_fft = fft_vals / np.sum(fft_vals) if np.sum(fft_vals) > 0 else np.ones_like(fft_vals) / len(fft_vals)
        spectral_entropy = -np.sum(normalized_fft * np.log2(normalized_fft + 1e-12))

        try:
            mfcc_features = mfcc(signal_values.reshape(-1, 1), samplerate=sampling_rate, numcep=13)
            mfcc_mean = mfcc_features.mean(axis=0).tolist()
        except Exception:
            mfcc_mean = [0.0] * 13

        # AUDIO FREQUENCY FEATURES:
        # // ENOB: Effective number of bits

        # DB (_sgnl): decibels
        # SNR: Signal-to-noise ratio
        # THD: Total harmonic distortion
        # THD + N: Total harmonic distortion plus noise

        # SFDR: Spurious free dynamic range
        # SINAD: Signal-to-noise-and-distortion ratio


        return {
            "dominant_freq": float(dominant_freq),
            "spectral_entropy": float(spectral_entropy),
            "fft_magnitude": fft_vals_50.tolist(),
            "mfcc": mfcc_mean
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

        # AUDIO FREQUENCY FEATURES:
        # // ENOB: Effective number of bits

        # DB (_sgnl): decibels
        # SNR: Signal-to-noise ratio
        # THD: Total harmonic distortion
        # THD + N: Total harmonic distortion plus noise

        # SFDR: Spurious free dynamic range
        # SINAD: Signal-to-noise-and-distortion ratio


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

    def __init__(self, audio_data=None, sampling_rate=None):
        self._audio_data = audio_data
        self._sr = sampling_rate
        self._frequency_features = None
        if audio_data is not None and sampling_rate is not None:
            self._frequency_features = self.compute_audio_frequency_features()

    def set_audio_data(self, audio_data, sampling_rate):
        """Set the audio data and sampling rate, and compute the frequency features."""
        self._audio_data = audio_data
        self._sr = sampling_rate
        self._frequency_features = self.compute_audio_frequency_features()

    def get_audio_data(self):
        """Get the audio data."""
        return self._audio_data

    def get_sampling_rate(self):
        """Get the sampling rate."""
        return self._sr

    def get_frequency_features(self):
        """Get the computed frequency features."""
        return self._frequency_features

    def compute_audio_frequency_features(self):
        """Compute frequency features for the given audio data."""
        return self.extract_audio_features(self._audio_data, self._sr)









# Get RMS value from each frame's magnitude value
# S, phase = librosa.magphase(librosa.stft(x))
# rms = librosa.feature.rms(S=S)# Plot the RMS energy

# TEMPOGRAM
# oenv = librosa.onset.onset_strength(y=x, sr=sr, hop_length=hop_length)
# times = librosa.times_like(oenv, sr=sr, hop_length=hop_length)
# tempogram = librosa.feature.tempogram(onset_envelope=oenv, sr=sr,
#                                       hop_length=hop_length)# Estimate the global tempo for display purposes
# tempo = librosa.feature.rhythm.tempo(onset_envelope=oenv, sr=sr, hop_length=hop_length)[0]
#
# fig, ax = plt.subplots(figsize=(15, 3))
# img = librosa.display.specshow(tempogram, x_axis='time', y_axis='tempo', hop_length=hop_length, cmap='coolwarm')
# fig.colorbar(img, ax=ax)


# def frame_audio(audio, FFT_size=2048, hop_size=10, sample_rate=44100):
#     # hop_size in ms
#
#     audio = np.pad(audio, int(FFT_size / 2), mode='reflect')
#     frame_len = np.round(sample_rate * hop_size / 1000).astype(int)
#     frame_num = int((len(audio) - FFT_size) / frame_len) + 1
#     frames = []  # np.zeros((frame_num,FFT_size))
#
#     for n in range(frame_num):
#         frame_len_n = n * frame_len
#         plus_FFT_size = n * frame_len + FFT_size
#
#         # frames[n] = audio[frame_len_n:plus_FFT_size]
#         # print("frame_len:", frame_len)
#         # print("frame_len_n:", frame_len_n)
#         # print("plus_FFT_size:", plus_FFT_size)
#         # print("result:", audio[frame_len_n:plus_FFT_size].shape)
#
#         # frames[n] = audio[frame_len_n:plus_FFT_size]
#         frames.append(audio[frame_len_n:plus_FFT_size])
#
#     framed_audio = np.array(frames)
#
#     print(frame_audio)
#
#     return framed_audio
#
# udio_framed = frame_audio(x, FFT_size=FFT_size, hop_size=hop_length, sample_rate=sr)
#
# # this controls the size and type of window used to
# # create the fft bins
# window = get_window("hann", FFT_size, fftbins=True)
#
# # plt.figure(figsize=(15,4))
# # plt.plot(window)
# # plt.grid(True)
#
#
# audio_win = audio_framed * window
#
# print("Framed audio shape: {0}".format(audio_framed.shape))
# print("First frame:", audio_framed[1])
# print("Last frame:", audio_framed[-1])
# print("audio_win.shape",audio_win.shape)
#
# plt.figure(figsize=(20,6))
# # plt.subplot(2, 1, 1)
# plt.plot(audio_framed)
# plt.title('Original Frame')
# plt.grid(True)
#
# # plt.subplot(2, 1, 2)
# plt.plot(audio_win)
# plt.title('Frame After Windowing')
# plt.grid(True)
#
# audio_winT = np.transpose(audio_win)
# print("audio_winT.shape", audio_winT.shape)
#
# audio_fft = np.empty((int(1 + FFT_size // 2), audio_winT.shape[1]), dtype=np.complex64, order='F')
#
# for n in range(audio_fft.shape[1]):
#     audio_fft[:, n] = fft.fft(audio_winT[:, n], axis=0)[:audio_fft.shape[0]]
#
# audio_fft = np.transpose(audio_fft)
#
# audio_power = np.square(np.abs(audio_fft))
# print("audio_power.shape", audio_power.shape)