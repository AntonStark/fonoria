from datetime import datetime

import matplotlib as mpl
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import numpy as np
import scipy.fftpack

from storage_helpers import audio_data, spectrum_data

mpl.rcParams['figure.subplot.left'] = 0.065
mpl.rcParams['figure.subplot.right'] = 0.935
mpl.rcParams['figure.subplot.top'] = 0.94
mpl.rcParams['axes.xmargin'] = 0


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

    fund_freq_by_fourier()

def plot_intense(ax):
    intense = audio_data.intensities()
    norm = intense / np.linalg.norm(intense, np.inf)

    ax.plot(audio_data._timeline, norm)
    ax.grid()
    ax.figure.canvas.draw()


def plot_spectrum(ax1, ax2):
    spectrum, spec_extent = spectrum_data.get(), spectrum_data.get_extent()
    z = 10. * np.log10(spectrum)
    z = np.flipud(z)

    ax1.imshow(z, plt.magma(), extent=spec_extent, aspect='auto')
    ax1.figure.canvas.draw()

    ax2.imshow(z, plt.magma(), extent=spec_extent, aspect='auto')
    ax2.plot(time, result, color='g')
    ax2.set_ylim(bottom=0, top=512)
    ax2.figure.canvas.draw()


def plot_momentum_spectrum(ax, part_of_duration):
    intensity = spectrum_data.get_moment_spectr(part_of_duration)
    ax.plot(np.linspace(0, 4096, intensity.size), intensity)
    ax.set_yscale('log', basey=10)
    ax.grid()
    ax.figure.canvas.draw()


def fr_fourier(part_of_duration):
    intensity = spectrum_data.get_moment_spectr(part_of_duration)
    four = scipy.fftpack.fft(intensity)
    fig, ax = plt.subplots()
    ax.plot(np.abs(four))
    plt.show()


def fund_freq_by_fourier():
    freq_high, freq_low = 8, 40
    spectrum = spectrum_data.get()
    result = []
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
            result.append(arg_max1 + freq_high)
        else:
            result.append(0)

    result = np.array(result)
    global time, result
    result = np.array(4096 / result)
    time = np.arange(0, spectrum.shape[1]*0.016, 0.016)


def print_tones(part_of_duration):
    intensity = spectrum_data.get_moment_spectr(part_of_duration)
    global result
    fund_fr = result[int(part_of_duration * result.shape[0])]
    print('f=', fund_fr, end='\t')

    def pick_nth_tone_magnitude(n):
        nonlocal fund_fr
        pick = [int(abs(fr - n*fund_fr) < fund_fr/4) for fr in range(0, 4096+1, 16)]
        nonlocal intensity
        return np.math.log10(sum([p*i for p, i in zip(pick, intensity)]))

    tones = [pick_nth_tone_magnitude(n) for n in range(0, 20)]
    tones_rel = tones / np.min(tones)
    # plt.plot(tones_rel, 'r.')
    # plt.show()
    print(['{:.2f}'.format(t) for t in tones_rel])

