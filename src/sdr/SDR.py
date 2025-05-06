# continuous spectrogram spectrum from stick (use demo_waterfall.py as base).
# find frequencies in the spectrogram that fit a model (avg db, snr, on, etc...)
# assign a worker to monitor the frquencies that fit the model.
# - worker records, catalogs signal when receiving a broadccast on assigned frequency
# - workers with signals are displayed in the spectrogram UI.


from __future__ import division
import matplotlib.animation as animation
from matplotlib.mlab import psd
import pylab as pyl
import numpy as np
import sys
from rtlsdr import RtlSdr

# A simple waterfall, spectrum plotter

NFFT = 1024*4
NUM_SAMPLES_PER_SCAN = NFFT*16
NUM_BUFFERED_SWEEPS = 100

# change this to control the number of scans that are combined in a single sweep
# (e.g. 2, 3, 4, etc.) Note that it can slow things down
NUM_SCANS_PER_SWEEP = 1

# these are the increments when scrolling the mouse wheel or pressing '+' or '-'
FREQ_INC_COARSE = 1e6
FREQ_INC_FINE = 0.1e6
GAIN_INC = 5

class Waterfall(object):
    image_buffer = -100*np.ones((NUM_BUFFERED_SWEEPS, NUM_SCANS_PER_SWEEP*NFFT))

    def __init__(self, sdr=None, fig=None):
        self.image = None
        self.ax = None
        self.fig = fig if fig else pyl.figure()
        self.sdr = sdr if sdr else RtlSdr()
        self.init_plot()

    def init_plot(self):
        print(f'called init_plot')
        self.ax = self.fig.add_subplot(1,1,1)
        self.image = self.ax.imshow(self.image_buffer, aspect='auto',\
                                    interpolation='nearest', vmin=-50, vmax=10)
        self.ax.set_xlabel('Current frequency (MHz)')
        self.ax.get_yaxis().set_visible(False)

    def update_plot_labels(self):
        print(f'called update_plot_labels')
        fc = self.sdr.fc
        rs = self.sdr.rs
        freq_range = (fc - rs/2)/1e6, (fc + rs*(NUM_SCANS_PER_SWEEP - 0.5))/1e6

        self.image.set_extent(freq_range + (0, 1))

    def update(self, *args):
        # save center freq. since we're gonna be changing it
        print(f'called update')
        start_fc = self.sdr.fc

        # prepare space in buffer
        # TODO: use indexing to avoid recreating buffer each time
        self.image_buffer = np.roll(self.image_buffer, 1, axis=0)

        for scan_num, start_ind in enumerate(range(0, NUM_SCANS_PER_SWEEP*NFFT, NFFT)):
            self.sdr.fc += self.sdr.rs*scan_num

            # estimate PSD for one scan
            samples = self.sdr.read_samples(NUM_SAMPLES_PER_SCAN)
            print(samples.shape)
            psd_scan, f = psd(samples, NFFT=NFFT)

            self.image_buffer[0, start_ind: start_ind+NFFT] = 10*np.log10(psd_scan)

        # plot entire sweep
        self.image.set_array(self.image_buffer)

        # restore original center freq.
        self.sdr.fc = start_fc

        return self.image,

    def start(self):
        print(f'called start')
        self.update_plot_labels()
        if sys.platform == 'darwin':
            blit = False
        else:
            blit = True

        ani = animation.FuncAnimation(self.fig, self.update, interval=50, blit=blit)

        pyl.show()
        return

def main():
    print(f'called main')
    sdr = RtlSdr()
    wf = Waterfall(sdr)

    # some defaults
    sdr.rs = 2.4e6
    sdr.fc = 100e6
    sdr.gain = 10

    wf.start()
    sdr.close()


if __name__ == '__main__':
    main()

