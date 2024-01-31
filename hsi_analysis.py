import csv
import os
import sys
import json
import glob

import numpy as np

from pathlib import Path
from PyQt5.QtWidgets import QApplication

from visualization.visualizer import HSIViewer
from hsi_processor import HSIProcessor


def get_average_spectrum(measurement_path, coordinates, kernel_size=1):

    processor = HSIProcessor()
    measurement, _ = processor.load_measurement(measurement_path)

    image = processor.measurement_2_arr(measurement)
    distance = int(kernel_size/2)

    if kernel_size <= 1:
        area_pixel = image[coordinates[0], coordinates[1], :]
    else:
        bot = coordinates[0]-distance
        top = coordinates[0]+distance
        area_pixel = image[coordinates[0]-distance:coordinates[0]+distance+1,
                           coordinates[1]-distance:coordinates[1]+distance+1, :]

    avg_spectrum = np.mean(area_pixel, axis=(0,1))

    return None

def read_annotations(csv_path):
    annotations = []
    with open(csv_path, 'r') as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            annotations.append(row)

    return annotations


def map_annotations_to_images(hsi_dic, annotation_list):

    data_dict = {}

    for annotation in annotation_list:

        image_paths = hsi_dic[annotation[5]][annotation[4]]
        mapped_image = None

        for path in image_paths:
            if annotation[0] in path:
                mapped_image = path

        annotation_dict = {'image_path': mapped_image,
                           'patient_id': annotation[5],
                           'body_part': annotation[4],
                           'annotation_type': annotation[3],
                           'coordinates': (int(annotation[1]), int(annotation[2]))}

        if annotation[0] not in data_dict:
            data_dict.update({annotation[0]: {0:annotation_dict}})
        else:
            data_dict[annotation[0]].update({len(data_dict[annotation[0]]): annotation_dict})

    return data_dict


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


if __name__ == "__main__":
    image_dir = "C:\\Users\\Martin\\Desktop\\preliminary_work\\2023_11_21_10-37-01\\images"
    annotation_file = "C:\\Users\\Martin\\Desktop\\preliminary_work\\point_annotations\\point_annotations.csv"

    hsi_dict = group_cu3s_files(image_dir)
    annotations = read_annotations(annotation_file)

    hsi_data_dict = map_annotations_to_images(hsi_dict, annotations)

    sample_measurement = hsi_data_dict[list(hsi_data_dict.keys())[0]][0]['image_path']
    coords = hsi_data_dict[list(hsi_data_dict.keys())[0]][0]['coordinates']
    spectrum = get_average_spectrum(sample_measurement, coords, kernel_size=3)

    # TODO: Create function to map annotations and images
    # TODO: Create function to aggregate by patient, localization.
    # TODO: UMAP plots over locations, patients, lesions

    print("fin")
