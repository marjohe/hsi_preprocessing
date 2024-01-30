import os
import sys
import json
import glob

import numpy as np

from PyQt5.QtWidgets import QApplication

from visualization.visualizer import HSIViewer
from hsi_processor import HSIProcessor


def save_json(dict, path):
    with open(path, 'w') as json_file:
        json.dump(dict, json_file)

def group_cu3s_files(base_dir):
    file_dict = {}

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

    return file_dict


def annotate(hsi_dict, annotation_type, out_dir):

    json_path = os.path.join(out_dir, annotation_type+'.json')
    annotated_dict = {}
    processor = HSIProcessor()
    wavelengths = processor.get_wavelengths()

    for patient_id, patient_dict in hsi_dict.items():
        annotated_dict.update({patient_id: {}})
        for body_part, image_list in patient_dict.items():
            annotated_dict[patient_id].update({body_part: {}})
            i = 0
            for image in image_list:
                annotated_dict[patient_id][body_part].update({i: {}})
                measurement, session = processor.load_measurement(image)
                hsi = processor.measurement_2_arr(measurement)

                ex = HSIViewer(hsi, wavelengths)
                ex.show()


                coords = ex.get_coordinates()

                image_dict = {'image_path': image, 'annotation_type': annotation_type, 'coordinates': coords}
                annotated_dict[patient_id][body_part][i].update(image_dict)

            save_json(annotated_dict, json_path)

    return annotated_dict


if __name__ == "__main__":
    image_dir = "C:\\Users\\C140_Martin\\Downloads\\2023_11_21_10-37-01(1)\\images"
    out_dir = "C:\\Users\\C140_Martin\\Desktop\\hsi_annotations"
    hsi_dict = group_cu3s_files(image_dir)

    annotated_dict = annotate(hsi_dict, 'skin', out_dir)

    print("fin")