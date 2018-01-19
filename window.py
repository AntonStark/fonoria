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

        self.btnRecord.clicked.connect(self.btnRecordClicked)

    def btnRecordClicked(self):
        seconds = self.boxDuration.value()
        self.rawData = record(seconds)
        self.rawAmplitudeGraph = plot(self.rawData)
        self.lblRawSound.setPixmap(self.rawAmplitudeGraph)
        print("debug")

def record(duration):
    CHUNK = 1000
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 40000
    RECORD_SECONDS = duration
    WAVE_OUTPUT_FILENAME = "output.wav"

    print("2...")
    time.sleep(1)
    print("1...")
    time.sleep(1)

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Recording...")

    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Done recording.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    b = []
    for f in frames:
        b.append(np.frombuffer(f, dtype=np.int16))

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    return np.ravel(b)

def plot(data):
    plt.figure(figsize=[5, 0.4])
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
