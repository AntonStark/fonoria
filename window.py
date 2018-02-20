import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtGui import QImage, QPixmap

import pyaudio, time, wave
import numpy as np
import numpy.ma as ma
import matplotlib.pyplot as plt
from datetime import datetime
import math

qtCreatorFile = "./mainwindow.ui"  # Путь к UI файлу

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class MyApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.audioParams = {
            'CHUNK': 1024,
            'FORMAT': pyaudio.paInt32,
            'CHANNELS': 1,
            'RATE': 8192,
            'WAVE_OUTPUT_FILENAME': "output.wav",
            'DURATION': self.boxDuration.value()}

        self.btnRecord.clicked.connect(self.btn_record_clicked)
        self.btnPlay.clicked.connect(self.btn_play_clicked)
        self.use_subs_spectrum = False
        self.chkSubsConst.stateChanged.connect(self.check_subs_const)
        self.boxDuration.valueChanged.connect(self.reset_duration)
        self.momentSelector.valueChanged.connect(self.refresh_momentum_spectrum)

    def reset_duration(self, dur):
        self.audioParams['DURATION'] = dur

    def print_progress(self, sec):
        dur = self.audioParams['DURATION']
        self.btnRecord.setText('{}/{}'.format(sec, dur))
        self.repaint()

    def btn_record_clicked(self):
        self.btnRecord.setText('3..')
        self.repaint()
        time.sleep(0.5)
        self.btnRecord.setText('2.')
        self.repaint()
        time.sleep(0.5)
        self.btnRecord.setText('1')
        self.repaint()
        time.sleep(0.5)

        self.print_progress(0)
        self.rawData = record(self.audioParams, self.print_progress)
        self.btnRecord.setText('Запись')
        self.btnPlay.setEnabled(True)
        self.momentSelector.setEnabled(True)
        # self.momentSelector.setMaximum = self.audioParams['DURATION'] * 64 - 3

        self.rawAmplitudeGraph = plot(self.rawData)
        self.lblRawAmplitude.setPixmap(self.rawAmplitudeGraph)

        start = datetime.now()
        self.spectrum = calc_spectrum(self.rawData[1], self.audioParams['RATE'])
        calc_time = datetime.now() - start

        self.lblRawSpectrum.setPixmap(self.spectrum[0])
        self.lblCalcTime.setText('FFT ~ {}мс.'
                                 .format(calc_time.microseconds / 1000))

    def btn_play_clicked(self):
        play(self.rawData[1], self.audioParams)

    def check_subs_const(self, state):
        self.use_subs_spectrum = (state == 2)
        if (self.use_subs_spectrum):
            self.subs_spectrum = substract_constant(self.spectrum[1])
        self.refresh_momentum_spectrum(self.moment_index)

    def refresh_momentum_spectrum(self, moment_index):
        self.moment_index = moment_index
        if (self.use_subs_spectrum):
            spectr = self.subs_spectrum
        else:
            spectr = self.spectrum[1]
        self.lblMomentumSpectrum.setPixmap(get_momentum_spectrum(spectr, moment_index / 10000))


def record(audioParams, print_progress):
    chunk = audioParams['CHUNK']
    format = audioParams['FORMAT']
    channels = audioParams['CHANNELS']
    rate = audioParams['RATE']
    duration = audioParams['DURATION']

    p = pyaudio.PyAudio()

    stream = p.open(format=format,
                    channels=channels,
                    rate=rate,
                    input=True,
                    frames_per_buffer=chunk)

    frames = []

    fps = rate / chunk
    n_frames = int(fps * duration)
    remainder = rate * duration - chunk * n_frames

    print_progress(0)
    old_sed = 0
    for i in range(0, n_frames):
        data = stream.read(chunk)
        frames.append(data)

        sec = int(i / fps)
        if sec != old_sed:
            print_progress(sec)
            old_sed = sec

    data = stream.read(remainder)
    frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    intensities = np.array([], dtype=np.int32)
    for f in frames:
        intensities = np.append(intensities, np.frombuffer(f, dtype=np.int32))

    t = np.arange(0.0, duration, 1.0 / rate)

    # wave_out_filename = audioParams['WAVE_OUTPUT_FILENAME']
    # wf = wave.open(wave_out_filename, 'wb')
    # wf.setnchannels(channels)
    # wf.setsampwidth(p.get_sample_size(format))
    # wf.setframerate(rate)
    # wf.writeframes(b''.join(frames))
    # wf.close()

    return t, intensities


def play(data, audio_params):
    chunk = audio_params['CHUNK']
    format = audio_params['FORMAT']
    channels = audio_params['CHANNELS']
    rate = audio_params['RATE']

    p = pyaudio.PyAudio()

    stream = p.open(format=format,
                    channels=channels,
                    rate=rate,
                    output=True,
                    frames_per_buffer=chunk)

    stream.write(data, data.size)

    stream.stop_stream()
    stream.close()
    p.terminate()


def plot(data):
    t, I = data
    norm = I / np.linalg.norm(I, np.inf)
    fig = plt.figure(figsize=[5, 0.8], frameon=False)
    ax = fig.add_subplot(111)
    ax.plot(t, norm)
    ax.margins(0, 0.1)
    ax.set_ylim(-1, 1)

    canvas = fig.canvas
    canvas.draw()
    buf = canvas.tostring_rgb()
    (width, height) = canvas.get_width_height()
    im = QImage(buf, width, height, QImage.Format_RGB888)
    return QPixmap(im)


def substract_constant(spectrum):
    copy = np.copy(spectrum)
    for frequency_level in copy:
        frequency_level -= np.min(frequency_level)
    return copy


def calc_spectrum(data, rate):
    # t = np.arange(0.0, 3.0, 2.**-13.)
    # s2 = 2 * np.sin(2 * np.pi * 200 * t)
    fig = plt.figure(figsize=[5, 2.5], frameon=False)
    ax = fig.add_subplot(111)

    spectrum, freqs, t, im = plt.specgram(data, Fs=rate,
                                          NFFT=512, noverlap=384,
                                          detrend='none', cmap=plt.magma())

    ax.set_yscale('log', basey=2)
    ax.set_ylim(64, 4096)

    canvas = plt.gcf().canvas
    canvas.draw()
    buf = canvas.tostring_rgb()
    (width, height) = canvas.get_width_height()
    im = QImage(buf, width, height, QImage.Format_RGB888)
    return QPixmap(im), spectrum


def get_family_harmonics(freqs, freq_step, chosen_f, h):
    lower_f = chosen_f - freq_step/2
    upper_f = chosen_f + freq_step/2
    fund_lower = int(lower_f / h)
    fund_upper = int(upper_f / h) + 1
    delta_fund = (fund_upper - fund_lower)/2 / (fund_lower + fund_upper)/2

    approx_match = []
    if delta_fund < 0.05:
        for f in freqs:
            if f <= int(f / fund_lower) * fund_upper:
                approx_match.append(f)

    return [fund_lower, fund_upper], approx_match


def eval_fund(freqs, fund_lower_bound, fund_upper_bound, freq_step):
    fund_lower_bound -= fund_lower_bound % freq_step
    fund_upper_bound += freq_step - fund_upper_bound % freq_step

    fund_diaps = {}
    for f in freqs:
        magn = math.log10(f[1])
        prob_harmonic_min = max(int(f[0] / fund_upper_bound), 1)
        prob_harmonic_max = int(f[0] / fund_lower_bound)
        if prob_harmonic_max < 3:
            continue    # хотим иметь хотя бы две кратных вниз, иначе низкая точность

        for h in range(prob_harmonic_max, prob_harmonic_min, -1):
            fund_low, fund_high = (f[0] - freq_step/2)/h, (f[0] + freq_step/2)/h
            fund_diaps[fund_low], fund_diaps[fund_high] = magn, -magn

    sum = 0
    x = []
    y = []
    sor = sorted(fund_diaps.items(), key=lambda i: i[0])
    for d in sor:
        sum += d[1]
        x.append(d[0])
        y.append(sum)
    fig = plt.figure(figsize=[4, 4], frameon=False)
    ax = fig.add_subplot(111)
    ax.plot(x, y)
    fig.show()

    fund = 0

    return fund


def analyse_spectrum(intensity):
    freq_step = 16
    fund_lower_bound = 80
    fund_upper_bound = 300
    n_main_comp = 30

    indices = np.arange(intensity.size)
    ind_round = int(fund_lower_bound / freq_step / 2)

    important = []
    intensity = ma.masked_where(indices < fund_lower_bound / freq_step, intensity)
    for n in range(0, n_main_comp):
        max_intensity = np.argmax(intensity)
        important.append((max_intensity * freq_step, intensity.max()))
        intensity = ma.masked_where(abs(indices - max_intensity) <= ind_round, intensity)

    freq = np.array(important)[:, 0]

    print('seq_search: ' + str(sequential_search(freq, freq_step, fund_lower_bound, fund_upper_bound)))

    return freq, eval_fund(important, fund_lower_bound, fund_upper_bound, freq_step)


def calc_intersect(fund_min, fund_max, band_left, band_right):
    right_corner = fund_max * int(band_left/fund_min)
    next_left_corner = fund_min * (int(band_left/fund_min)+1)
    intersect = 0
    if band_left < right_corner:
        intersect += min(band_right, right_corner) - band_left
        if band_right > next_left_corner:
            intersect += band_right - next_left_corner
    else:
        if band_right > next_left_corner:
            next_right_corner = fund_max * (int(band_left/fund_min)+1)
            intersect += min(next_right_corner, band_right) - next_left_corner
    intersect /= band_right - band_left
    return intersect


def analyse_bands(intensity, freq_step, lower_bound, upper_bound, n_parts):
    total_energy = math.fsum(intensity)
    width = (upper_bound - lower_bound) / n_parts
    statistics = {}
    for p in range(0, n_parts):
        chosen_energy, ch = 0, 0
        freq_min = lower_bound + p * width
        freq_max = freq_min + width
        for f in range(0, intensity.size):
            freq = f * freq_step
            inter = calc_intersect(freq_min, freq_max, freq - freq_step/2, freq + freq_step/2)
            chosen_energy += intensity[f] * inter
            ch += inter
        statistics[(freq_min, freq_max)] = chosen_energy/total_energy / ch/intensity.size
    print(sorted(statistics.items(), key=lambda i: i[1]))


def drop_out_noise(important, delta_freq):
    а = []
    """ 
    Для каждой пары частот проверяем, что найдётся третья кратная.
    Для начала, решим эту задачу как будто частоты известны точно
    """


def sequential_search(freqs, freq_step, lower_bound, upper_bound):
    fund = lower_bound
    count = 0
    for w in range(upper_bound, lower_bound, -1):
        new_count = 0
        for f in freqs:
            if f % w < freq_step/2 or w - f % w < freq_step/2:
                new_count += 1
        if new_count > count:
            fund = w
            count = new_count
    return fund


def get_momentum_spectrum(spectrum, part_of_duration):
    n_frames = int(part_of_duration * spectrum.shape[1])

    fig = plt.figure(figsize=[4, 4], frameon=False)
    ax = fig.add_subplot(111)
    intensity = spectrum[:, n_frames]
    ax.plot(np.linspace(0, 4096, intensity.size), intensity)
    ax.set_yscale('log', basey=10)
    ax.grid()

    freqs, fund = analyse_spectrum(intensity)
    for x in freqs:
        ax.axvline(x, color='green')
    print(fund)

    analyse_bands(intensity, 16, 80, 300, 100)

    canvas = fig.canvas
    canvas.draw()
    buf = canvas.tostring_rgb()
    (width, height) = canvas.get_width_height()
    im = QImage(buf, width, height, QImage.Format_RGB888)
    return QPixmap(im)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
