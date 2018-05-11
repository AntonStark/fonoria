import os
import sys
import time

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication
from matplotlib.backends.backend_qt5agg import (
    FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure

import process
import sound_operations
from storage_helpers import audio_data, spectrum_data

qtCreatorFile = "./mainwindow.ui"  # Путь к UI файлу
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


def show_folders():
    all_subfolders = next(os.walk('.'))[1]
    visible = [d for d in all_subfolders if not d.startswith('.') and not d.startswith('_')]
    visible.append('.')
    return visible


def show_wav_files(folder):
    files = next(os.walk(folder))[2]
    files = [f for f in files if f.endswith('.wav')]
    return files


class MyApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.plot_axs = self.init_plots()
        self.spectrum_ax = self.init_spectrums()

        self.btnRecord.clicked.connect(self.btn_record_clicked)
        self.btnPlay.clicked.connect(self.btn_play_clicked)
        self.btnSave.clicked.connect(self.btn_save_clicked)
        self.btnOpen.clicked.connect(self.btn_open_clicked)

        self.boxMode.activated[str].connect(self.switch_input_mode)
        self.boxFolder.activated[str].connect(self.update_box_files)
        self.boxSpectr.activated[str].connect(self.switch_spectrum_mode)

        self.lineFilename.hide()
        self.toggle_file_mode()

        self.btnFrFourier.clicked.connect(self.fr_fourier)
        self.btnTones.clicked.connect(self.print_tones)

        self.time_moment = 0
        self.part_of_duration = 0

    def set_time(self, time):
        self.time_moment = time
        self.part_of_duration = self.time_moment / audio_data._duration
        self.lblMomentum.setText("t={0:.2f}".format(self.time_moment))

    def switch_input_mode(self, mode):
        if mode == 'файл':
            self.toggle_file_mode()
        elif mode == 'запись':
            self.toggle_record_mode()

    def update_box_files(self, folder):
        files = show_wav_files(folder)
        self.boxFile.clear()
        self.boxFile.addItems(files)

    def toggle_file_mode(self):
        prev_ind, prev_val = self.boxFolder.currentIndex(), self.boxFolder.currentText()

        folders = show_folders()
        self.boxFolder.clear()
        self.boxFolder.addItems(folders)
        if prev_val in folders:
            self.boxFolder.setCurrentIndex(prev_ind)

        self.update_box_files(self.boxFolder.currentText())

        self.frameFile.show()
        self.frameRecord.hide()

    def toggle_record_mode(self):
        self.frameFile.hide()
        self.frameRecord.show()

    def toggle_audio_loaded_state(self):
        self.btnPlay.setEnabled(True)
        self.set_time(0)

        process.calc_spectrum()
        self.refresh_plots()

    def btn_record_clicked(self):
        def print_progress(text):
            self.btnRecord.setText(text)
            self.btnRecord.repaint()

        for mess in ['3..', '2.', '1']:
            print_progress(mess)
            time.sleep(0.5)

        sound_operations.record(self.boxDuration.value(), print_progress)
        self.btnRecord.setText('Запись')
        self.toggle_audio_loaded_state()

    def btn_play_clicked(self):
        sound_operations.play()

    def btn_save_clicked(self):
        if not self.lineFilename.isVisible():
            self.lineFilename.show()
        else:
            filename = self.lineFilename.text()
            if not filename.endswith('.wav'):
                filename += '.wav'
                sound_operations.save(filename)
            self.lineFilename.clear()
            self.lineFilename.hide()

    def btn_open_clicked(self):
        folder, file = self.boxFolder.currentText(), self.boxFile.currentText()
        if file != '':
            sound_operations.open_(folder + '/' + file)

        self.toggle_audio_loaded_state()

    def switch_spectrum_mode(self, sp_mode):
        if sp_mode == 'исходный':
            spectrum_data.set_use_raw()
        elif sp_mode == 'нормализованный':
            spectrum_data.set_use_subs()
        elif sp_mode == 'сглаженная нормализация':
            spectrum_data.set_use_subs_smoothed()

        self.refresh_plots()

    def init_plots(self):
        plots = FigureCanvas(Figure(figsize=(7, 7)))
        self.plotsLayout.addWidget(plots)
        self.plotsLayout.addWidget(NavigationToolbar(plots, self))

        fig = plots.figure
        axs = fig\
            .subplots(3, 1, sharex='col', gridspec_kw={'height_ratios': [1, 3, 2]})

        axs[0].set_ylim(-1, 1)
        for ax in axs:
            ax.grid()

        def on_click(event):
            if not event.inaxes:
                return
            time = event.xdata
            self.set_time(time)
            self.refresh_momentum_spectrum()
        fig.canvas.mpl_connect('button_press_event', on_click)

        return axs

    def init_spectrums(self):
        plots = FigureCanvas(Figure(figsize=(4, 4)))
        self.spectrumLayout.insertWidget(0, plots)

        fig = plots.figure
        ax = fig.subplots(1, 1, sharex='col')

        # for ax in axs:
        #     ax.grid()
        ax.grid()

        return ax

    def refresh_plots(self):
        for ax in self.plot_axs:
            ax.clear()

        process.plot_intense(self.plot_axs[0])
        process.plot_spectrum(self.plot_axs[1], self.plot_axs[2])
        self.refresh_momentum_spectrum()

    def refresh_momentum_spectrum(self):
        self.spectrum_ax.clear()
        process.plot_momentum_spectrum(self.spectrum_ax, self.part_of_duration)

    def fr_fourier(self):
        process.fr_fourier(self.part_of_duration)

    def print_tones(self):
        process.print_tones(self.part_of_duration)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
