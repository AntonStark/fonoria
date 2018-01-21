import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtGui import QImage, QPixmap

import pyaudio, time, wave
import numpy as np
import matplotlib.pyplot as plt

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
            'RATE' : 8096,
            'WAVE_OUTPUT_FILENAME' : "output.wav",
            'DURATION' : self.boxDuration.value()}

    def btnRecordClicked(self):
        self.rawData = record(self.audioParams)

        self.btnPlay.setEnabled(True)
        self.rawAmplitudeGraph = plot(self.rawData)
        self.lblRawAmplitude.setPixmap(self.rawAmplitudeGraph)
        self.lblRawSpectrum.setPixmap(
            calcSpectrum(self.rawData, self.audioParams['RATE']))

    def btnPlayClicked(self):
        play(self.rawData, self.audioParams)

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

    for i in range(0, int(rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)

    print("Done recording.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    b = []
    for f in frames:
        b.append(np.frombuffer(f, dtype=np.int32))

    wf = wave.open(wave_out_filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()

    return np.ravel(b)

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
    norm = data / np.linalg.norm(data, np.inf)
    fig = plt.figure(figsize=[5, 0.8], frameon=False)
    ax = fig.add_subplot(111)
    ax.plot(norm)

    canvas = fig.canvas
    canvas.draw()
    buf = canvas.tostring_rgb()
    (width, height) = canvas.get_width_height()
    im = QImage(buf, width, height, QImage.Format_RGB888)
    return QPixmap(im)

def calcSpectrum(data, rate):
    # t = np.arange(0.0, 3.0, 00013)
    # s2 = 2 * np.sin(2 * np.pi * 400 * t)
    fig = plt.figure(figsize=[5, 1.6], frameon=False)
    ax = fig.add_subplot(111)
    spectrum, freqs, t, im = plt.specgram(data, Fs=rate,
                                          NFFT=512, noverlap=384,
                                          detrend='none', cmap=plt.magma())

    canvas = plt.gcf().canvas
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

def btn(data, audioParams):
    # roughN = 200
    # accurateN = 800
    # deltaT_ms = 10

    # deltaX = audioParams['RATE'] / 1000 * deltaT_ms
    # frame = 0
    # offset = int(deltaX * frame)
    # while offset + roughN < data.size:
    rate = audioParams['RATE']
    spectrum, freqs, t, im = plt.specgram(data, Fs=rate, detrend='none')
    plt.show()
