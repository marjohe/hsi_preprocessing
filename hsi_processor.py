import os
import platform

import cuvis

import sys
import numpy as np
import matplotlib.pyplot as plt


class HSIProcessor:
    def __init__(self):
        self.wavelengths = np.linspace(450, 950, 51)

    def get_wavelengths(self):
        return self.wavelengths

    @staticmethod
    def measurement_2_arr(measurement):
        cube = measurement.data.get("cube", None)
        if cube is None:
            raise Exception("Cube not found")

        if measurement.processing_mode.name == 'Reflectance':
            return cube.array/10000
        else:
            return cube.array

    @staticmethod
    def load_measurement(measurement_path):
        try:
            session = cuvis.SessionFile(measurement_path)
            measurement = session[0]
            assert measurement._handle
        except Exception as e:
            print(e)
            return None

        return measurement, session

    def set_calibration(self, dark_ref, white_ref):
        session_dark = cuvis.SessionFile(dark_ref)
        self.dark = session_dark[0]
        assert self.dark._handle

        session_white = cuvis.SessionFile(white_ref)
        self.white = session_white[0]
        assert self.white._handle

    def raw2reflectance(self, measurement_session, dark_ref=None, white_ref=None):
        measurement = measurement_session[0]
        assert measurement._handle

        if dark_ref is None:
            dark = self.dark
        else:
            session_dark = cuvis.SessionFile(dark_ref)
            dark = session_dark[0]
            assert dark._handle

        if white_ref is None:
            white = self.white
        else:
            session_white = cuvis.SessionFile(white_ref)
            white = session_white[0]
            assert white._handle

        processing_context = cuvis.ProcessingContext(measurement_session)

        processing_context.set_reference(dark, cuvis.ReferenceType.Dark)
        processing_context.set_reference(white, cuvis.ReferenceType.White)

        proc_args = cuvis.ProcessingArgs()

        proc_args.processing_mode = cuvis.ProcessingMode.Reflectance

        processing_context.set_processing_args(proc_args)
        reflectance_measurement = processing_context.apply(measurement)

        return reflectance_measurement


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.realpath(__file__))
    ref_path = os.path.join(script_dir, "resources", "ref.cu3s")
    raw_path = os.path.join(script_dir, "resources", "raw.cu3s")
    torso_lesion = os.path.join(script_dir, "resources", "torso_lesion.cu3s")

    dark_ref_path = "C:\\Users\\Martin\\Downloads\\preliminary_work\\2023_11_21_10-37-01\\dark.cu3s"
    white_ref_path = "C:\\Users\\Martin\\Downloads\\preliminary_work\\2023_11_21_10-37-01\\white.cu3s"

    mesu_path = torso_lesion

    processor = HSIProcessor()

    measuremnt, sess = processor.load_measurement(mesu_path)

    hsi = processor.measurement_2_arr(measuremnt)

    print("fin")
