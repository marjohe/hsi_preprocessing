import os
import sys
import json
import glob

import numpy as np

from PyQt5.QtWidgets import QApplication

from visualization.visualizer import HSIViewer
from hsi_processor import HSIProcessor



def read_annotation(file_path):

    file = open(file_path, 'r')
    content = file.readlines()

    return content

def map_annotations_to_images(hsi_dict, annotation_dir):
    pass

def annotations_to_csv(annotation_dir):
    annotations = []

    for patient in os.listdir(annotation_dir):
        for localization in os.listdir(os.path.join(annotation_dir,patient)):
            for image in os.listdir(os.path.join(annotation_dir, patient, localization)):
                for file in os.listdir(os.path.join(annotation_dir, patient, localization, image)):

                    content = read_annotation(os.path.join(annotation_dir, patient, localization, image, file))
                    print(image)



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
    image_dir = "C:\\Users\\C140_Martin\\Desktop\\hsi_test_data\\images"
    annotation_dir = "C:\\Users\\C140_Martin\\Desktop\\hsi_test_data\\annotations"

    hsi_dict = group_cu3s_files(image_dir)
    annotations_to_csv(annotation_dir)

    # TODO: Create function to map annotations and images
    # TODO: Function to parse annotation files
    # TODO: Create function to aggregate by patient, localization.
    # TODO: UMAP plots over locations, patients, lesions

    print("fin")
