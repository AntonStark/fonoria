import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtGui import QImage, QPixmap

import pyaudio, time, wave
import numpy as np
import numpy.ma as ma
import matplotlib.pyplot as plt
from datetime import datetime

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

    def refresh_momentum_spectrum(self, moment_index):
        self.lblMomentumSpectrum.setPixmap(get_momentum_spectrum(self.spectrum[1], moment_index / 10000))


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


def eval_fund(freqs, fund_lower_bound, fund_upper_bound, freq_step):
    """"""
    fund_lower_bound -= fund_lower_bound % freq_step
    fund_upper_bound += freq_step - fund_upper_bound % freq_step
    part_matches = 0.6

    """ 
        Перебираем допустимый номер гармоники. От большего к меньшему,
        потому что нужно максимальное совпадение по частотам. А если так и 
        не было сопадения - выкидываем из частот. Совпадение с учётом 
        приблизительности определения частоты.
    """
    freqs = np.sort(freqs)
    for f in reversed(freqs):
        n_harmonic = int(f / fund_upper_bound)
        N_harmonic = int(f / fund_lower_bound)

    # for fund in range(fund_upper_bound, fund_lower_bound - 1, -1):
    #     mismatch, match = 0, 0
    #     for freq in reversed(freqs):
    #         if (freq % fund > freq_step/2) and (fund - freq % fund > freq_step/2):
    #             mismatch += 1
    #             if mismatch >= (1 - part_matches) * freqs.size:
    #                 break
    #         else:
    #             match += 1
    #             if match >= part_matches * freqs.size:
    #                 return fund
    return 0


def analyse_spectrum(intensity):
    freq_step = 16
    fund_lower_bound = 50
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

    return freq, eval_fund(freq, fund_lower_bound, fund_upper_bound, freq_step)


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
