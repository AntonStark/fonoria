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

qtCreatorFile = "./mainwindow.ui"  # Путь к UI файлу

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class MyApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.plot_axs = self.init_plots()

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

        sound_operations.record(self.boxDuration.value(), self.print_progress)
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
        folder = self.boxFolder.currentText()
        file = self.boxFile.currentText()
        if file != '':
            sound_operations.open_(folder + '/' + file)

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

        return axs

    def refresh_plots(self):
        for ax in self.plot_axs:
            ax.clear()

        process.plot_intense(self.plot_axs[0])
        process.plot_spectrum(self.plot_axs[1], self.plot_axs[2])
        self.refresh_momentum_spectrum(self.momentSelector.value())

        self.plot_axs[0].figure.canvas.draw()


    def fr_fourier(self):
        part_of_duration = self.momentSelector.value()
        process.fr_fourier(part_of_duration/10000)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
