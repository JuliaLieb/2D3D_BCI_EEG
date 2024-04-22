
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import mne
from mne.time_frequency import tfr_multitaper
from mne.stats import permutation_cluster_1samp_test as pcluster_test
import os
import scipy.io
import glob
from PyQt5.QtWidgets import QApplication
import sys

from FeedbackModel import xdf_to_mat


if __name__ == "__main__":
    cwd = os.getcwd()
    data_path = cwd + '/../SubjectDataSorted/'

    # ----- Define Subject and Session ----
    subject_id = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'S10', 'S11', 'S12', 'S13', 'S14', 'S14', 'S15']
    session_id = [0, 1, 2]
    # -------------------------------------

    # Transform all xdf files to mat files for the given config files in the Subject-Session-folder
    for current_subject in subject_id:
        for current_session in session_id:
            subject_directory = data_path + current_subject + '-ses' + str(current_session) + '/'
            all_config_files = glob.glob(subject_directory + '*.json')

            for current_config_file in all_config_files:
                with open(current_config_file) as json_file:
                    config = json.load(json_file)
                xdf_to_mat.xdf_to_mat_new(config, data_path)

    # Show raw eeg data
