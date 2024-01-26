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
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Hyperspectral Image Viewer')
        self.setGeometry(100, 100, 800, 600)

        # Create a matplotlib plot
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        # Slider for selecting channels
        self.slider = QSlider(self)
        self.slider.setOrientation(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(self.image.shape[2] - 1)
        self.slider.setValue(0)
        self.slider.valueChanged[int].connect(self.change_value)

        # Label for slider
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.label)
        layout.addWidget(self.slider)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.update_plot(0)

    def change_value(self, value):
        self.update_plot(value)
        self.label.setText(f'Channel: {value}')

    def update_plot(self, channel):

        self.ax.clear()
        self.ax.imshow(self.image[:, :, channel], cmap='gray')
        self.ax.set_title(f'Peak wavelength {self.wavelengths[channel]} nm')
        self.canvas.draw()

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.realpath(__file__))
    ref_path = os.path.join(script_dir, "..", "resources", "ref.cu3s")
    raw_path = os.path.join(script_dir, "..", "resources", "raw.cu3s")
    torso_lesion = os.path.join(script_dir, "..", "resources", "torso_lesion.cu3s")

    dark_ref_path = "C:\\Users\\Martin\\Downloads\\preliminary_work\\2023_11_21_10-37-01\\dark.cu3s"
    white_ref_path = "C:\\Users\\Martin\\Downloads\\preliminary_work\\2023_11_21_10-37-01\\white.cu3s"

    mesu_path = torso_lesion

    processor = HSIProcessor()

    measurement, session = processor.load_measurement(mesu_path)

    hsi = processor.measurement_2_arr(measurement)
    wavelengths = processor.get_wavelengths()
    print("fin")
    app = QApplication(sys.argv)
    ex = HSIViewer(hsi, wavelengths)
    ex.show()
    sys.exit(app.exec_())