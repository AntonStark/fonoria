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

        self.btnRecord.clicked.connect(self.btn_record_clicked)
        self.btnPlay.clicked.connect(self.btn_play_clicked)
        self.btnSave.clicked.connect(self.btn_save_clicked)
        self.btnOpen.clicked.connect(self.btn_open_clicked)

        self.lineFilename.hide()
        self.use_subs_spectrum = False
        self.chkSubsConst.stateChanged.connect(self.check_subs_const)
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

    def print_progress(self, sec, dur):
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

        record(self.boxDuration.value(), self.print_progress)
        self.btnRecord.setText('Запись')
        self.btnPlay.setEnabled(True)
        self.momentSelector.setEnabled(True)

        self.rawAmplitudeGraph = plot()
        self.lblRawAmplitude.setPixmap(self.rawAmplitudeGraph)

        start = datetime.now()
        self.spectrum = process.calc_spectrum(process.audio_data._intensities, process.audio_data.rate())
        calc_time = datetime.now() - start

        self.lblRawSpectrum.setPixmap(self.spectrum[0])
        self.lblCalcTime.setText('FFT ~ {}мс.'
                                 .format(calc_time.microseconds / 1000))

    def btn_play_clicked(self):
        play()

    def btn_save_clicked(self):
        if not self.lineFilename.isVisible():
            self.lineFilename.show()
        else:
            filename = self.lineFilename.text()
            if not filename.endswith('.wav'):
                filename += '.wav'
            save(filename)
            self.lineFilename.clear()
            self.lineFilename.hide()

    def btn_open_clicked(self):
        print('asd')

    def check_subs_const(self, state):
        self.use_subs_spectrum = (state == 2)
        if self.use_subs_spectrum:
            self.subs_spectrum = process.subtract_constant(self.spectrum[1])
        self.refresh_momentum_spectrum(self.moment_index)

    def refresh_momentum_spectrum(self, moment_index):
        self.moment_index = moment_index
        if self.use_subs_spectrum:
            spectrum = self.subs_spectrum
        else:
            spectrum = self.spectrum[1]
        self.lblMomentumSpectrum.setPixmap(process.get_momentum_spectrum(spectrum, moment_index / 10000))


def record(duration, print_progress):
    ad = process.audio_data
    p = pyaudio.PyAudio()

    stream = p.open(format=ad.format(),
                    channels=ad.channels(),
                    rate=ad.rate(),
                    input=True,
                    frames_per_buffer=ad.chunk())

    frames = []

    fps = ad.rate() / ad.chunk()
    n_frames = int(fps * duration)
    remainder = ad.rate() * duration - ad.chunk() * n_frames

    print_progress(0, duration)
    old_sed = 0
    for i in range(0, n_frames):
        data = stream.read(ad.chunk())
        frames.append(data)

        sec = int(i / fps)
        if sec != old_sed:
            print_progress(sec, duration)
            old_sed = sec

    data = stream.read(remainder)
    frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    process.audio_data.set_data(frames, duration)


def save(filename):
    ad = process.audio_data
    frames = ad._frames

    wf = wave.open(filename, 'wb')
    wf.setnchannels(ad.channels())
    wf.setsampwidth(pyaudio.PyAudio()
                    .get_sample_size(ad.format()))
    wf.setframerate(ad.rate())
    wf.writeframes(b''.join(frames))
    wf.close()


def play():
    ad = process.audio_data
    p = pyaudio.PyAudio()

    stream = p.open(format=ad.format(),
                    channels=ad.channels(),
                    rate=ad.rate(),
                    output=True,
                    frames_per_buffer=ad.chunk())

    data = process.audio_data._intensities
    stream.write(data, data.size)

    stream.stop_stream()
    stream.close()
    p.terminate()


def plot():
    intense = process.audio_data._intensities
    norm = intense / np.linalg.norm(intense, np.inf)
    fig = plt.figure(figsize=[5, 0.8], frameon=False)
    ax = fig.add_subplot(111)
    ax.plot(process.audio_data._timeline, norm)
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
