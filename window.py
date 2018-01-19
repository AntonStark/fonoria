import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtGui import QImage, QPixmap

import pyaudio, time, wave
import numpy as np
import matplotlib.pyplot as plt

qtCreatorFile = "qtgui/mainwindow.ui"  # Путь к UI файлу

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class MyApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.setAudioParams()
        self.btnRecord.clicked.connect(self.btnRecordClicked)
        self.btnPlay.clicked.connect(self.btnPlayClicked)

    def setAudioParams(self):
        self.audioParams = {
            'CHUNK' : 1000,
            'FORMAT' : pyaudio.paInt16,
            'CHANNELS' : 1,
            'RATE' : 40000,
            'WAVE_OUTPUT_FILENAME' : "output.wav"}

    def btnRecordClicked(self):
        seconds = self.boxDuration.value()
        self.rawData = record(seconds, self.audioParams)
        self.rawAmplitudeGraph = plot(self.rawData)
        self.lblRawSound.setPixmap(self.rawAmplitudeGraph)

    def btnPlayClicked(self):
        play(self.rawData, self.audioParams)

def record(duration, audioParams):
    chunk = audioParams['CHUNK']
    format = audioParams['FORMAT']
    channels = audioParams['CHANNELS']
    rate = audioParams['RATE']
    wave_out_filename = audioParams['WAVE_OUTPUT_FILENAME']
    audioParams['DURATION'] = duration

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
        b.append(np.frombuffer(f, dtype=np.int16))

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
    duration = audioParams['DURATION']

    p = pyaudio.PyAudio()

    stream = p.open(format=format,
                    channels=channels,
                    rate=rate,
                    output=True,
                    frames_per_buffer=chunk)

    stream.write(data, rate * duration)

    stream.stop_stream()
    stream.close()
    p.terminate()

def plot(data):
    plt.figure(figsize=[5, 0.6])
    # todo настроить оси
    plt.plot(data)
    plt.savefig('wave.png', fmt='png')

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
