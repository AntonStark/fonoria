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
import os

import process

qtCreatorFile = "./mainwindow.ui"  # Путь к UI файлу

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class MyApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.audio_params = {
            'CHUNK': 1024,
            'FORMAT': pyaudio.paInt32,
            'CHANNELS': 1,
            'RATE': 8192,
            'DURATION': self.boxDuration.value()}
        self.raw_frames = []

        self.btnRecord.clicked.connect(self.btn_record_clicked)
        self.btnPlay.clicked.connect(self.btn_play_clicked)
        self.btnSave.clicked.connect(self.btn_save_clicked)
        self.btnOpen.clicked.connect(self.btn_open_clicked)

        self.lineFilename.hide()
        self.use_subs_spectrum = False
        self.chkSubsConst.stateChanged.connect(self.check_subs_const)
        self.boxDuration.valueChanged.connect(self.reset_duration)
        self.momentSelector.valueChanged.connect(self.refresh_momentum_spectrum)

        self.toggle_file_mode()
        self.boxMode.activated[str].connect(self.switch_input_mode)
        self.boxFolder.activated[str].connect(self.show_files)

    def switch_input_mode(self, mode):
        if mode == 'файл':
            self.toggle_file_mode()
        elif mode == 'запись':
            self.toggle_record_mode()

    def show_files(self, directory):
        files = next(os.walk(directory))[2]
        files = [f for f in files if f.endswith('.wav')]

        self.boxFile.clear()
        self.boxFile.addItems(files)

    def toggle_file_mode(self):
        prev_ind, prev_val = self.boxFolder.currentIndex(), self.boxFolder.currentText()

        all_subdirs = next(os.walk('.'))[1]
        visible = [d for d in all_subdirs if not d.startswith('.')]
        visible.append('.')

        self.boxFolder.clear()
        self.boxFolder.addItems(visible)
        if prev_val in visible:
            self.boxFolder.setCurrentIndex(prev_ind)
        self.show_files(self.boxFolder.currentText())

        self.frameFile.show()
        self.frameRecord.hide()

    def toggle_record_mode(self):
        self.frameFile.hide()
        self.frameRecord.show()

    def reset_duration(self, dur):
        self.audio_params['DURATION'] = dur

    def print_progress(self, sec):
        dur = self.audio_params['DURATION']
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
        self.rawData = record(self.audio_params, self.print_progress)
        self.raw_frames = self.rawData[2]
        self.btnRecord.setText('Запись')
        self.btnPlay.setEnabled(True)
        self.momentSelector.setEnabled(True)
        # self.momentSelector.setMaximum = self.audioParams['DURATION'] * 64 - 3

        self.rawAmplitudeGraph = plot(self.rawData)
        self.lblRawAmplitude.setPixmap(self.rawAmplitudeGraph)

        start = datetime.now()
        self.spectrum = process.calc_spectrum(self.rawData[1], self.audio_params['RATE'])
        calc_time = datetime.now() - start

        self.lblRawSpectrum.setPixmap(self.spectrum[0])
        self.lblCalcTime.setText('FFT ~ {}мс.'
                                 .format(calc_time.microseconds / 1000))

    def btn_play_clicked(self):
        play(self.rawData[1], self.audio_params)

    def btn_save_clicked(self):
        if not self.lineFilename.isVisible():
            self.lineFilename.show()
        else:
            filename = self.lineFilename.text()
            if not filename.endswith('.wav'):
                filename += '.wav'
            save(self.audio_params, self.raw_frames, filename)
            self.lineFilename.clear()
            self.lineFilename.hide()

    def btn_open_clicked(self):
        print('asd')

    def check_subs_const(self, state):
        self.use_subs_spectrum = (state == 2)
        if (self.use_subs_spectrum):
            self.subs_spectrum = process.subtract_constant(self.spectrum[1])
        self.refresh_momentum_spectrum(self.moment_index)

    def refresh_momentum_spectrum(self, moment_index):
        self.moment_index = moment_index
        if (self.use_subs_spectrum):
            spectrum = self.subs_spectrum
        else:
            spectrum = self.spectrum[1]
        self.lblMomentumSpectrum.setPixmap(process.get_momentum_spectrum(spectrum, moment_index / 10000))


def record(audio_params, print_progress):
    chunk = audio_params['CHUNK']
    format = audio_params['FORMAT']
    channels = audio_params['CHANNELS']
    rate = audio_params['RATE']
    duration = audio_params['DURATION']

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

    return t, intensities, frames


def save(audio_params, frames, filename):
    format = audio_params['FORMAT']
    channels = audio_params['CHANNELS']
    rate = audio_params['RATE']

    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(pyaudio.PyAudio()
                    .get_sample_size(format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()


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
    t, I, f = data
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
