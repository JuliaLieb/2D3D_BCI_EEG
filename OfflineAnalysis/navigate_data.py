
import json
import numpy as np
import matplotlib.pyplot as plt
#from matplotlib.colors import TwoSlopeNorm
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

    ''' Comment out if all .mat exist
    # Transform all xdf files to mat files for the given config files in the Subject-Session-folder
    # ----- Define Subject and Session ----
    subject_id = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'S10', 'S11', 'S12', 'S13', 'S14', 'S14', 'S15', 'S16', 'S17']
    session_id = [0, 1, 2]
    # -------------------------------------
    
    for current_subject in subject_id:
        for current_session in session_id:
            subject_directory = data_path + current_subject + '-ses' + str(current_session) + '/'
            all_config_files = glob.glob(subject_directory + '*.json')

            for current_config_file in all_config_files:
                with open(current_config_file) as json_file:
                    config = json.load(json_file)
                xdf_to_mat.xdf_to_mat_new(config, data_path)
    '''

    # Get .mat files per session
    #'''
    subject_id = 'S14'
    session_id = 1
    runs = [1,2,3,4,5]

    subject_data_path = data_path + subject_id + '-ses' + str(session_id) + '/'

    all_mat_files = []

    for r in runs:
        for file in os.listdir(subject_data_path):
            if file.startswith(subject_id + '_run' + str(r)):
                if file.endswith('.mat'):
                    all_mat_files.append(file)
    #'''

    # Get specific run
    run_id = 2
    current_mat = [i for i in all_mat_files if i.startswith(subject_id + '_run' + str(run_id))]

    # Print raw EEG






