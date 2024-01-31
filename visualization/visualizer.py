import sys
import os
import glob

import matplotlib.pyplot as plt

from PyQt5.QtWidgets import QApplication, QMainWindow, QSlider, QLabel, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtWidgets import QDialog, QLineEdit, QMessageBox
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


from hsi_processor import HSIProcessor


class AnnotationDialog(QDialog):
    def __init__(self, parent=None):
        super(AnnotationDialog, self).__init__(parent)
        self.setWindowTitle('Enter Annotation Details')
        self.setGeometry(100, 100, 300, 200)

        self.annotation_type = QLineEdit(self)
        self.location = QLineEdit(self)
        self.patient = QLineEdit(self)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Annotation Type:'))
        layout.addWidget(self.annotation_type)
        layout.addWidget(QLabel('Location:'))
        layout.addWidget(self.location)
        layout.addWidget(QLabel('Patient:'))
        layout.addWidget(self.patient)

        self.save_button = QPushButton('Save', self)
        self.save_button.clicked.connect(self.accept)
        layout.addWidget(self.save_button)

    def get_details(self):
        return self.annotation_type.text(), self.location.text(), self.patient.text()



class HSIViewer(QMainWindow):
    def __init__(self, file_list, annotation_dir=""):
        super().__init__()
        self.hsi_processor = HSIProcessor()
        self.file_list = file_list
        self.images = self.load_images(file_list)  # List of hyperspectral images
        self.wavelengths = self.hsi_processor.get_wavelengths()
        self.current_image_index = 0  # Index of the current image being viewed
        self.last_clicked_point = None
        self.annotation_dir = annotation_dir
        self.initUI()

    def load_images(self, file_list):
        hsi_list = []
        for file in file_list:
            measurement,_ = self.hsi_processor.load_measurement(file)
            hsi  =self.hsi_processor.measurement_2_arr(measurement)
            hsi_list.append(hsi)
        return hsi_list

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
        self.slider.setMaximum(self.images[0].shape[2] - 1)
        self.slider.setValue(0)
        self.slider.valueChanged[int].connect(self.changeValue)

        # Label for slider
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)

        # Coordinate label
        self.coord_label = QLabel(self)
        self.coord_label.setAlignment(Qt.AlignCenter)

        # Initialize the QLabel for displaying the current file name
        self.file_name_label = QLabel(self)
        self.file_name_label.setAlignment(Qt.AlignCenter)

        # Create a Save Coordinates Button
        self.save_coord_button = QPushButton('Save Coordinates', self)
        self.save_coord_button.clicked.connect(self.save_coordinates)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.label)
        layout.addWidget(self.coord_label)
        layout.addWidget(self.slider)
        layout.addWidget(self.save_coord_button)

        # Buttons for navigating images
        self.prev_button = QPushButton('Previous Image', self)
        self.prev_button.clicked.connect(self.prev_image)
        self.next_button = QPushButton('Next Image', self)
        self.next_button.clicked.connect(self.next_image)

        # Update layout
        layout.addWidget(self.prev_button)
        layout.addWidget(self.next_button)
        layout.addWidget(self.file_name_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.update_plot(0)
        self.update_file_name_label()

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
        current_image = self.images[self.current_image_index]
        self.ax.clear()
        self.ax.imshow(current_image[:, :, channel], cmap='gray')
        if self.last_clicked_point:
            x, y = self.last_clicked_point
            self.ax.add_patch(plt.Rectangle((x - 0.5, y - 0.5), 1, 1, edgecolor='red', facecolor='none'))

            # Plotting the spectrum
            self.spectrum_ax.clear()
            self.spectrum_ax.plot(self.wavelengths, current_image[y, x, :])
            self.spectrum_ax.set_ylim([0,1])
            self.spectrum_ax.set_title('Spectrum at '+ f'{y,x}')
            self.spectrum_ax.set_xlabel('Wavelength (nm)')
            self.spectrum_ax.set_ylabel('Reflectance')

            # Marking the selected wavelength on the spectrum
            selected_wavelength = self.wavelengths[channel]
            self.spectrum_ax.axvline(x=selected_wavelength, color='red', linestyle='--')
            self.spectrum_ax.text(selected_wavelength, max(current_image[y, x, :]), f'{selected_wavelength} nm', color='red')

        self.ax.set_title(f'Peak wavelength {self.wavelengths[channel]} nm')
        self.canvas.draw()

    def update_file_name_label(self):
        file_name = self.file_list[self.current_image_index]
        self.file_name_label.setText(f'Current Image: {file_name}')

    def get_coordinates(self):
        return self.last_clicked_point

    def changeImage(self, index):
        self.current_image_index = index
        self.update_plot(self.slider.value())
        self.update_file_name_label()

    def prev_image(self):
        if self.current_image_index > 0:
            self.changeImage(self.current_image_index - 1)

    def next_image(self):
        if self.current_image_index < len(self.images) - 1:
            self.changeImage(self.current_image_index + 1)

    def save_coordinates(self):
        if self.last_clicked_point is not None:
            dialog = AnnotationDialog(self)
            if dialog.exec_():
                annotation_type, location, patient = dialog.get_details()
                annotation_dir = os.path.join(self.annotation_dir, patient, location)
                if not os.path.exists(annotation_dir):
                    os.makedirs(annotation_dir)
                with open(annotation_dir+'\\'+annotation_type+'.txt', 'a') as file:
                    file.write(f"{self.file_list[self.current_image_index]}, {self.last_clicked_point}, {annotation_type}, {location}, {patient}\n")
                QMessageBox.information(self, "Annotation Saved", "Annotation saved successfully.")
        else:
            QMessageBox.warning(self, "No Coordinates", "No coordinates to save. Please click on the image first.")



def group_cu3s_files(base_dir):
    file_dict = {}
    file_list = []
    # Walk through the directory
    for root, dirs, files in os.walk(base_dir):
        # Skip the root directory itself
        if root == base_dir:
            continue

        # Extract patient name and body part from the path
        parts = root.split(os.sep)
        if len(parts) >= 3:
            patient_name = parts[-2]
            body_part = parts[-1]

            # Find all .cu3s files in the current directory
            cu3s_files = glob.glob(os.path.join(root, '*.cu3s'))

            # Add to dictionary
            if cu3s_files:
                file_dict.setdefault(patient_name, {}).setdefault(body_part, []).extend(cu3s_files)
                for file in cu3s_files:
                    file_list.append(file)

    return file_dict, file_list


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.realpath(__file__))
    image_dir = "C:\\Users\\C140_Martin\\Desktop\\hsi_test_data\\small"
    torso_lesion = "C:\\Users\\C140_Martin\\Downloads\\2023_11_21_10-37-01\\p4\\stomach\\Auto_006_3284.cu3s"
    annotation_dir = "C:\\Users\\C140_Martin\\Desktop\\hsi_test_data\\annotations"

    mesu_path = torso_lesion
    processor = HSIProcessor()
    wavelengths = processor.get_wavelengths()

    hsi_dict, file_list = group_cu3s_files(image_dir)

    app = QApplication(sys.argv)
    ex = HSIViewer(file_list, annotation_dir)
    ex.show()
    sys.exit(app.exec_())
