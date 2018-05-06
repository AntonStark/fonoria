import os
import sys

import pyaudio
import time
import wave
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication

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

        self.boxMode.activated[str].connect(self.switch_input_mode)
        self.boxFolder.activated[str].connect(self.show_files)
        self.boxSpectr.activated[str].connect(self.switch_spectrum_mode)

        self.momentSelector.valueChanged.connect(self.refresh_momentum_spectrum)
        self.lineFilename.hide()
        self.toggle_file_mode()

        self.btnFrFourier.clicked.connect(self.fr_fourier)

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

    def toggle_audio_loaded_state(self):
        self.btnPlay.setEnabled(True)
        self.momentSelector.setEnabled(True)

        self.lblRawAmplitude.setPixmap(process.plot_intense())

        process.calc_spectrum()
        self.refresh_plots()

    def print_progress(self, sec, dur):
        self.btnRecord.setText('{}/{}'.format(sec, dur))
        self.repaint()

    def btn_record_clicked(self):
        for mess in ['3..', '2.', '1']:
            self.btnRecord.setText(mess)
            self.repaint()
            time.sleep(0.5)

        record(self.boxDuration.value(), self.print_progress)
        self.btnRecord.setText('Запись')
        self.toggle_audio_loaded_state()

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
        folder = self.boxFolder.currentText()
        file = self.boxFile.currentText()
        if file != '':
            open_(folder + '/' + file)

        self.toggle_audio_loaded_state()

    def switch_spectrum_mode(self, sp_mode):
        if sp_mode == 'исходный':
            process.spectrum_data.set_use_raw()
        elif sp_mode == 'нормализованный':
            process.spectrum_data.set_use_subs()
        elif sp_mode == 'сглаженная нормализация':
            process.spectrum_data.set_use_subs_smoothed()

        self.refresh_plots()

    def refresh_momentum_spectrum(self, moment_index):
        moment_index /= 10000
        self.lblMomentumSpectrum.setPixmap(process.get_momentum_spectrum(moment_index))
        self.lblMomentum.setText("{0:.2f}".format(moment_index * process.audio_data._duration))

    def refresh_plots(self):
        spec, spec_details = process.plot_spectrum()

        self.lblRawSpectrum.setPixmap(spec)
        self.lblRawSpectrum.resize(spec.size())

        self.lblRawSpectrum_details.setPixmap(spec_details)
        self.lblRawSpectrum_details.resize(spec_details.size())

        self.lblAmplitude.setPixmap(process.plot_intense_proc())

        self.refresh_momentum_spectrum(self.momentSelector.value())

    def fr_fourier(self):
        part_of_duration = self.momentSelector.value()
        process.fr_fourier(part_of_duration/10000)


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

    for i in range(0, n_frames):
        data = stream.read(ad.chunk())
        frames.append(data)

        sec = int(i / fps)
        print_progress(sec, duration)

    data = stream.read(remainder)
    frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    process.audio_data.set_data(frames)


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


def open_(filename):
    file = wave.open(filename, 'rb')
    n_frames = file.getnframes()

    parts, remainder = int(n_frames / 1024), n_frames % 1024
    frames = []
    for i in range(0, parts):
        data = file.readframes(1024)
        frames.append(data)
    if remainder != 0:
        data = file.readframes(remainder)
        frames.append(data)
    file.close()

    process.audio_data.reset_params(channels=file.getnchannels(), rate=file.getframerate())
    process.audio_data.set_data(frames)


def play():
    ad = process.audio_data
    p = pyaudio.PyAudio()

    stream = p.open(format=ad.format(),
                    channels=ad.channels(),
                    rate=ad.rate(),
                    output=True,
                    frames_per_buffer=ad.chunk())

    data = process.audio_data.intensities()
    stream.write(data, data.size)

    stream.stop_stream()
    stream.close()
    p.terminate()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
