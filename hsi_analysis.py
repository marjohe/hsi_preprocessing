import csv
import os
import sys
import json
import glob

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

import umap

from pathlib import Path
from PyQt5.QtWidgets import QApplication

from visualization.visualizer import HSIViewer
from hsi_processor import HSIProcessor


def create_UMAP(df):
    df_ref = df

    df_ref = df_ref[df_ref['annotation_type'] == 'skin']

    # Reshaping the DataFrame
    reshaped_df = df_ref.pivot_table(index=['patient_id', 'body_part'], columns='wavelength',
                                 values='reflectance').reset_index()

    # Extract features and target
    features = reshaped_df.drop(['body_part', 'patient_id'], axis=1).values
    body_parts = reshaped_df['body_part'].values
    #patient_ids = reshaped_df['patient_id'].values

    for metric in ['correlation']:
        for n in [5, 10, 20]:
            for d in (0.1, 0.15, 0.25, 0.5, 0.8):

                reducer = umap.UMAP(n_neighbors=n, min_dist=d, metric=metric)
                embedding = reducer.fit_transform(features)
                sns.set_theme(style="darkgrid")
                # Plot
                plt.figure(figsize=(10, 6))
                for body_part in set(body_parts):
                    indices = body_parts == body_part
                    plt.scatter(embedding[indices, 0], embedding[indices, 1], label=body_part)
                plt.title(f'UMAP plot with points colored by patient_id, metric={metric}, n={n},d={d}')
                plt.legend(title='Body part', loc='upper left')
                plt.show()



def dict2dataframe(data_dict):
    wavelengths = np.linspace(450, 950, 51)
    wavelength_columns = [int(w) for w in wavelengths]

    # Preparing data for DataFrame
    data_for_df = []
    for measurement_name, measurement in data_dict.items():
        for item in measurement.values():
            row = {
                'image_name': measurement_name,
                'patient_id': item['patient_id'],
                'body_part': item['body_part'],
                'annotation_type': item['annotation_type']
            }
            # Ensuring there are 51 reflectance values (padding with NaN if needed)
            reflectance_values = item['reflectance']
            row.update(dict(zip(wavelength_columns, reflectance_values)))
            data_for_df.append(row)

    # Creating the DataFrame
    df = pd.DataFrame(data_for_df)

    return df

def get_dataframe(spectra_array):

    # Setting column names as wavelengths
    column_names = np.linspace(450, 950, 51).astype(int).astype(str)

    df = pd.DataFrame(spectra_array, columns=column_names)

    # Reset index to get spectrum number as a column
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'Measurement'}, inplace=True)

    # Melt the DataFrame
    df_melted = df.melt(id_vars='Measurement', var_name='Wavelength', value_name='Reflectance')

    print(df_melted.head())

    df_melted['Wavelength'] = pd.to_numeric(df_melted['Wavelength'])

    print(df_melted.head())

    # Plotting
    sns.set_theme(style="darkgrid")

    sns.lineplot(data=df_melted, x='Wavelength', y='Reflectance', errorbar='sd')
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Reflectance')
    plt.title('Reflectance over Wavelength')
    plt.show()

    return df

def add_spectra(data, kernel_size=3):
    processor = HSIProcessor()

    for image_name, annotations in data.items():
        for annotation_number, details in annotations.items():
            measurement, _ = processor.load_measurement(details['image_path'])
            hsi = processor.measurement_2_arr(measurement)
            details['reflectance'] = get_average_spectrum(hsi, coordinates=details['coordinates'], kernel_size=kernel_size)

    return data


def extract_spectra(data, kernel_size=3):

    processor = HSIProcessor()
    spectra_arr = np.zeros(shape=(len(data), 51))

    i = 0
    for image_name, annotations in data.items():
        for annotation_number, details in annotations.items():

            measurement, _ = processor.load_measurement(details['image_path'])
            hsi = processor.measurement_2_arr(measurement)

            spectra_arr[i,:] = get_average_spectrum(hsi, coordinates=details['coordinates'], kernel_size=kernel_size)
            i += 1

    return spectra_arr


def filter_images(data, key1=None, value1=None, key2=None, value2=None):
    """
    Filters images based on up to two optional criteria in the dictionary, maintaining the original structure.

    :param data: The dictionary containing the image data.
    :param key1: The first key to filter on (e.g., 'annotation_type'), optional.
    :param value1: The specific value of the first key to filter on, optional.
    :param key2: The second key to filter on (e.g., 'body_part'), optional.
    :param value2: The specific value of the second key to filter on, optional.
    :return: A dictionary of filtered image data.
    """
    filtered_data = {}

    for image_name, annotations in data.items():
        for annotation_number, details in annotations.items():
            match1 = details.get(key1) == value1 if key1 is not None else True
            match2 = details.get(key2) == value2 if key2 is not None else True

            if match1 and match2:
                if image_name not in filtered_data:
                    filtered_data[image_name] = {}
                filtered_data[image_name][annotation_number] = details

    return filtered_data

def get_average_spectrum(hsi, coordinates, kernel_size=1):

    distance = int(kernel_size/2)

    if kernel_size <= 1:
        avg_spectrum = hsi[coordinates[1], coordinates[0], :]
    else:
        area_pixel = hsi[coordinates[1]-distance:coordinates[1]+distance+1,
                           coordinates[0]-distance:coordinates[0]+distance+1, :]
        avg_spectrum = np.mean(area_pixel, axis=(0,1))

    return avg_spectrum

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


def read_dataframe(xlsx_path):

    df = pd.read_excel(xlsx_path)
    df = df[df.columns[1:]]

    print(df.head())

    return df





if __name__ == "__main__":
    image_dir = "C:\\Users\\C140_Martin\\Desktop\\hsi_test_data\\images"
    annotation_file = "C:\\Users\\C140_Martin\\development\\hsi_preprocessing\\resources\\point_annotations.csv"
    """
    hsi_dict = group_cu3s_files(image_dir)
    annotations = read_annotations(annotation_file)

    hsi_data_dict = map_annotations_to_images(hsi_dict, annotations)

    print("Adding spectra...")
    spec_dict = add_spectra(hsi_data_dict, kernel_size=7)

    print("Creating dataframe...")
    df = dict2dataframe(spec_dict)

    """

    #df.to_excel("C:\\Users\\C140_Martin\\development\\hsi_preprocessing\\resources\\dataframe_k7.xlsx")
    df = read_dataframe("C:\\Users\\C140_Martin\\development\\hsi_preprocessing\\resources\\dataframe_k7.xlsx")

    #df = df[df['body_part'] == 'arms']
    #df = df[df['annotation_type'] == 'lesion']

    # Melt the DataFrame to have 'wavelength' and 'reflectance' columns
    df_melted = df.melt(id_vars=['image_name', 'patient_id', 'body_part', 'annotation_type'],
                        var_name='wavelength',
                        value_name='reflectance')

    # Convert wavelength to numeric if it's not already
    df_melted['wavelength'] = pd.to_numeric(df_melted['wavelength'])

    print(df_melted.head())
    #df_melted = df_melted[df_melted['annotation_type'] == 'skin']

    # Now you can plot using Seaborn

    sns.set_theme(style="darkgrid")

    # Example to plot error lines for 'lesion' annotation_type
    plt.figure(figsize=(14, 7))
    sns.lineplot(x='wavelength', y='reflectance',hue='annotation_type', data=df_melted, errorbar='sd')

    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Reflectance')
    plt.title('Reflectance over wavelength of normal skin')
    plt.legend()
    plt.show()
