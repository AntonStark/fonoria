import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtGui import QImage, QPixmap

import pyaudio, time, wave
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

qtCreatorFile = "./mainwindow.ui"  # Путь к UI файлу

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class MyApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.setAudioParams()
        self.btnRecord.clicked.connect(self.btnRecordClicked)
        self.btnPlay.clicked.connect(self.btnPlayClicked)
        self.boxDuration.valueChanged.connect(self.setAudioParams)

    def setAudioParams(self):
        self.audioParams = {
            'CHUNK' : 1024,
            'FORMAT' : pyaudio.paInt32,
            'CHANNELS' : 1,
            'RATE' : 8192,
            'WAVE_OUTPUT_FILENAME' : "output.wav",
            'DURATION' : self.boxDuration.value()}

    def btnRecordClicked(self):
        self.rawData = record(self.audioParams)

        self.btnPlay.setEnabled(True)
        self.rawAmplitudeGraph = plot(self.rawData)
        self.lblRawAmplitude.setPixmap(self.rawAmplitudeGraph)

        s = calcSpectrum(self.rawData[1], self.audioParams['RATE'])
        self.lblRawSpectrum.setPixmap(s[0])
        self.lblCalcTime.setText('FFT ~ {}мс.'
                                 .format(s[1].microseconds / 1000))

    def btnPlayClicked(self):
        play(self.rawData[1], self.audioParams)

def record(audioParams):
    chunk = audioParams['CHUNK']
    format = audioParams['FORMAT']
    channels = audioParams['CHANNELS']
    rate = audioParams['RATE']
    wave_out_filename = audioParams['WAVE_OUTPUT_FILENAME']
    duration = audioParams['DURATION']

    print("2...")
    time.sleep(1)
    print("1...")
    time.sleep(1)

    p = pyaudio.PyAudio()

    stream = p.open(format=format,
                    channels=channels,
                    rate=rate,
                    input=True,
                    frames_per_buffer=chunk)

    print("Recording...")

    frames = []
    nFrames = int(rate / chunk * duration)
    remainder = rate * duration - chunk * nFrames
    for i in range(0, nFrames):
        data = stream.read(chunk)
        frames.append(data)
    data = stream.read(remainder)
    frames.append(data)

    print("Done recording.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    I = np.array([], dtype=np.int32)
    for f in frames:
        I = np.append(I, np.frombuffer(f, dtype=np.int32))

    t = np.arange(0.0, duration, 1.0 / rate)
    # wf = wave.open(wave_out_filename, 'wb')
    # wf.setnchannels(channels)
    # wf.setsampwidth(p.get_sample_size(format))
    # wf.setframerate(rate)
    # wf.writeframes(b''.join(frames))
    # wf.close()


    return t, I

def play(data, audioParams):
    chunk = audioParams['CHUNK']
    format = audioParams['FORMAT']
    channels = audioParams['CHANNELS']
    rate = audioParams['RATE']

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

def calcSpectrum(data, rate):
    # t = np.arange(0.0, 3.0, 2.**-13.)
    # s2 = 2 * np.sin(2 * np.pi * 200 * t)
    fig = plt.figure(figsize=[5, 2.5], frameon=False)
    ax = fig.add_subplot(111)

    start = datetime.now()
    spectrum, freqs, t, im = plt.specgram(data, Fs=rate,
                                          NFFT=512, noverlap=384,
                                          detrend='none', cmap=plt.magma())
    calc_time = datetime.now() - start\

    ax.set_yscale('log', basey=2)
    ax.set_ylim(64, 4096)

    canvas = plt.gcf().canvas
    canvas.draw()
    buf = canvas.tostring_rgb()
    (width, height) = canvas.get_width_height()
    im = QImage(buf, width, height, QImage.Format_RGB888)
    return QPixmap(im), calc_time

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
