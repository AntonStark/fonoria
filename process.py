from datetime import datetime

import matplotlib as mpl
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import numpy as np
from PyQt5.QtGui import QImage, QPixmap
import scipy.fftpack

from storage_helpers import AudioData, SpectrumData

audio_data = AudioData()
spectrum_data = SpectrumData()

mpl.rcParams['figure.subplot.left'] = 0.065
mpl.rcParams['figure.subplot.right'] = 0.935
mpl.rcParams['figure.subplot.top'] = 0.94


def plot_intense():
    intense = audio_data.intensities()
    norm = intense / np.linalg.norm(intense, np.inf)

    fig = plt.figure(figsize=[7, 0.6])
    ax = fig.add_subplot(111)

    ax.plot(audio_data._timeline, norm)
    ax.margins(0, 0.1)
    ax.set_ylim(-1, 1)

    canvas = fig.canvas
    canvas.draw()
    buf = canvas.tostring_rgb()
    plt.close(fig)

    (width, height) = canvas.get_width_height()
    im = QImage(buf, width, height, QImage.Format_RGB888)
    return QPixmap(im)


def calc_spectrum():
    data = audio_data.intensities()
    nfft, noverlap, fs = 512, 384, audio_data.rate()

    start = datetime.now()
    spectr, freqs, t = mlab.specgram(data, Fs=fs, NFFT=nfft,
                                     noverlap=noverlap, detrend='none')
    calc_time = datetime.now() - start

    pad_xextent = (nfft - noverlap) / fs / 2
    xmin, xmax = np.min(t) - pad_xextent, np.max(t) + pad_xextent
    spec_extent = xmin, xmax, freqs[0], freqs[-1]

    spectrum_data.set(spectr, spec_extent)
    print('FFT ~ {}мс.'.format(calc_time.microseconds / 1000))


def plot_spectrum():
    spectrum, spec_extent = spectrum_data.get(), spectrum_data.get_extent()
    z = 10. * np.log10(spectrum)
    z = np.flipud(z)

    fig = plt.figure(figsize=[7, 3])
    ax = fig.add_subplot(111)
    canvas = fig.canvas

    plt.imshow(z, plt.magma(), extent=spec_extent, aspect='auto')

    canvas.draw()
    buf = canvas.tostring_rgb()
    (width, height) = canvas.get_width_height()
    im1 = QImage(buf, width, height, QImage.Format_RGB888)

    time, result = fund_freq_by_fourier()
    plt.plot(time, result, color='g')

    fig.set_size_inches(7, 1.2)
    ax.set_ylim(bottom=0, top=512)

    canvas.draw()
    buf = canvas.tostring_rgb()
    (width, height) = canvas.get_width_height()
    im2 = QImage(buf, width, height, QImage.Format_RGB888)

    plt.close(fig)
    return QPixmap(im1), QPixmap(im2)


def get_momentum_spectrum(part_of_duration):
    spectrum = spectrum_data.get()
    n_frame = int(part_of_duration * spectrum.shape[1])

    intensity = spectrum[:, n_frame]

    fig = plt.figure(figsize=[4, 4])
    ax = fig.add_subplot(111)
    ax.plot(np.linspace(0, 4096, intensity.size), intensity)
    ax.set_yscale('log', basey=10)
    ax.grid()

    # freqs, fund = analyse_spectrum(intensity)
    # for x in freqs:
    #     ax.axvline(x, color='green')
    # print(fund)

    # analyse_bands(intensity, 16, 80, 300, 100)

    canvas = fig.canvas
    canvas.draw()
    buf = canvas.tostring_rgb()
    (width, height) = canvas.get_width_height()
    plt.close(fig)

    im = QImage(buf, width, height, QImage.Format_RGB888)
    return QPixmap(im)

def plot_intense_proc():
    intense = spectrum_data.get_intense_processed()

    time = np.arange(0, audio_data._duration, 0.016)

    fig = plt.figure(figsize=[7, 0.6])
    ax = fig.add_subplot(111)

    ax.plot(time, intense)
    ax.margins(0, 0.1)
    # ax.set_ylim(-1, 1)

    canvas = fig.canvas
    canvas.draw()
    buf = canvas.tostring_rgb()
    plt.close(fig)

    (width, height) = canvas.get_width_height()
    im = QImage(buf, width, height, QImage.Format_RGB888)
    return QPixmap(im)


def fr_fourier(part_of_duration):
    spectrum = spectrum_data.get()
    n_frame = int(part_of_duration * spectrum.shape[1])

    intensity = spectrum[:, n_frame]
    four = scipy.fftpack.fft(intensity)
    fig, ax = plt.subplots()
    ax.plot(np.abs(four))
    plt.show()

def fund_freq_by_fourier():
    freq_high, freq_low = 8, 40
    spectrum = spectrum_data.get()
    result = np.array([])
    for i in range(0, spectrum.shape[1]):
        moment_spectrum = spectrum[:, i]
        freq_fourier = np.abs(scipy.fftpack.fft(moment_spectrum))
        intrest = freq_fourier[freq_high:freq_low]

        arg_max1 = np.argmax(intrest)
        max1 = intrest[arg_max1]
        intrest[arg_max1] = -np.inf
        arg_max2 = np.argmax(intrest)
        max2 = intrest[arg_max2]
        # print(abs(arg_max2-arg_max1), abs(max2-max1)/max2)
        if arg_max1 != 0:
            result = np.append(result, arg_max1 + freq_high)
        else:
            result = np.append(result, 0)

    result = 4096 / result
    time = np.arange(0, spectrum.shape[1]*0.016, 0.016)
    return time, result
