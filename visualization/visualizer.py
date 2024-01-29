import sys
import os

import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QSlider, QLabel, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import Qt

from hsi_processor import HSIProcessor


class HSIViewer(QMainWindow):
    def __init__(self, image, wavelengths):
        super().__init__()
        self.image = image
        self.wavelengths = wavelengths
        self.last_clicked_point = None  # Variable to store the last clicked point
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Hyperspectral Image Viewer')
        self.setGeometry(100, 100, 1200, 600)  # Adjusted window size

        # Create two matplotlib plots
        self.figure, (self.ax, self.spectrum_ax) = plt.subplots(1, 2, figsize=(12, 6))  # Two subplots
        self.canvas = FigureCanvas(self.figure)
        self.canvas.mpl_connect('button_press_event', self.on_click)

        # Slider for selecting channels
        self.slider = QSlider(self)
        self.slider.setOrientation(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(self.image.shape[2] - 1)
        self.slider.setValue(0)
        self.slider.valueChanged[int].connect(self.changeValue)

        # Label for slider
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)

        # Coordinate label
        self.coord_label = QLabel(self)
        self.coord_label.setAlignment(Qt.AlignCenter)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.label)
        layout.addWidget(self.coord_label)
        layout.addWidget(self.slider)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.update_plot(0)

    def changeValue(self, value):
        self.update_plot(value)
        self.label.setText(f'Channel: {value}')

    def on_click(self, event):
        if event.xdata is not None and event.ydata is not None:
            x, y = int(event.xdata), int(event.ydata)
            self.coord_label.setText(f'Coordinates: (X: {x}, Y: {y})')
            self.last_clicked_point = (x, y)  # Store the last clicked point
            self.update_plot(self.slider.value())  # Update the plot with the new point

    def update_plot(self, channel):
        self.ax.clear()
        self.ax.imshow(self.image[:, :, channel], cmap='gray')
        if self.last_clicked_point:
            x, y = self.last_clicked_point
            self.ax.add_patch(plt.Rectangle((x - 0.5, y - 0.5), 1, 1, edgecolor='red', facecolor='none'))

            # Plotting the spectrum
            self.spectrum_ax.clear()
            self.spectrum_ax.plot(self.wavelengths, self.image[y, x, :])
            self.spectrum_ax.set_title('Spectrum at '+ f'{y,x}')
            self.spectrum_ax.set_xlabel('Wavelength (nm)')
            self.spectrum_ax.set_ylabel('Intensity')

            # Marking the selected wavelength on the spectrum
            selected_wavelength = self.wavelengths[channel]
            self.spectrum_ax.axvline(x=selected_wavelength, color='red', linestyle='--')
            self.spectrum_ax.text(selected_wavelength, max(self.image[y, x, :]), f'{selected_wavelength} nm', color='red')

        self.ax.set_title(f'Peak wavelength {self.wavelengths[channel]} nm')
        self.canvas.draw()

    def get_coordinates(self):
        return self.last_clicked_point

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.realpath(__file__))

    torso_lesion = "C:\\Users\\C140_Martin\\Downloads\\2023_11_21_10-37-01\\p4\\stomach\\Auto_006_3284.cu3s"
    mesu_path = torso_lesion
    processor = HSIProcessor()

    measurement, session = processor.load_measurement(mesu_path)

    hsi = processor.measurement_2_arr(measurement)
    wavelengths = processor.get_wavelengths()
    app = QApplication(sys.argv)
    ex = HSIViewer(hsi, wavelengths)
    ex.show()
    sys.exit(app.exec_())
