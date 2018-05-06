import numpy as np
import pyaudio
import matplotlib.pyplot as plt
from enum import Enum


class AudioData:
    def __init__(self):
        self._chunk = 1024
        self._format = pyaudio.paInt32
        self._channels = 1
        self._rate = 8192
        self._duration = 3

        self._frames = []
        self._intensities = np.array([], dtype=np.int32)
        self._timeline = np.array([])

    def set_data(self, frames):
        self._frames = frames
        self._intensities = np.array([], dtype=np.int32)
        for f in frames:
            self._intensities = np.append(self._intensities, np.frombuffer(f, dtype=np.int32))
        self._duration = self._intensities.size / self._rate
        self._timeline = np.arange(0.0, self._duration, 1.0 / self._rate)

    def reset_params(self, **kwargs):
        changed = False
        for key, value in kwargs.items():
            if key == 'chunk':
                self._chunk, changed = value, True
            elif key == 'format':
                self._format, changed = value, True
            elif key == 'channels':
                self._channels, changed = value, True
            elif key == 'rate':
                self._rate, changed = value, True
        if changed:
            self._duration = 0
            self._frames = []
            self._intensities = np.array([], dtype=np.int32)
            self._timeline = np.array([])

    def chunk(self):
        return self._chunk

    def format(self):
        return self._format

    def channels(self):
        return self._channels

    def rate(self):
        return self._rate

    def intensities(self):
        return self._intensities


class SpectrumData:
    class Mode(Enum):
        RAW = 0
        SUBS = 1
        SUBS_SMOOTHED = 2

    def __init__(self):
        self._raw_spectrum = np.array([])
        self._subs_spectrum = None
        self._subs_smoothed = None

        self._spec_extent = None
        self._sensitivity = np.array([])
        self._sensitivity_smoothed = np.array([])

        self._use_mode = self.Mode(self.Mode.RAW)

    def _get_sensitivity_statistics(self):
        self._sensitivity = np.min(self._raw_spectrum, 1)

        def smooth(y, box_pts):
            box = np.ones(box_pts) / box_pts
            y_smooth = np.convolve(y, box, mode='same')
            return y_smooth

        self._sensitivity_smoothed = smooth(self._sensitivity, 20)

        # fig = plt.figure(figsize=[4, 4])
        # ax = fig.add_subplot(111)
        # ax.set_yscale('log', basey=10)
        #
        # ax.plot(np.arange(0, 4097, 16), self._sensitivity)
        # ax.plot(np.arange(0, 4097, 16), self._sensitivity_smoothed, 'r', lw=2)
        #
        # fig.show()

    def set(self, data, spec_extent):
        self._raw_spectrum = data
        self._spec_extent = spec_extent

        self._get_sensitivity_statistics()
        self._subs_spectrum = self._raw_spectrum / self._sensitivity[:, None]
        self._subs_smoothed = self._raw_spectrum / self._sensitivity_smoothed[:, None]

    def get(self):
        if self._use_mode == self.Mode.RAW:
            return self._raw_spectrum
        elif self._use_mode == self.Mode.SUBS:
            return self._subs_spectrum
        elif self._use_mode == self.Mode.SUBS_SMOOTHED:
            return self._subs_smoothed

    def get_extent(self):
        return self._spec_extent

    def get_intense_processed(self):
        spectr = self.get()
        return np.sum(spectr, 0)

    def set_use_raw(self):
        self._use_mode = self.Mode.RAW

    def set_use_subs(self):
        self._use_mode = self.Mode.SUBS

    def set_use_subs_smoothed(self):
        self._use_mode = self.Mode.SUBS_SMOOTHED
