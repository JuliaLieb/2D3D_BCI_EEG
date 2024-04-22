"""
Imports a xdf file and exports it to a .mat file.
"""

import json
import numpy as np
import os
import pyxdf
import scipy.io


def load_xdf(xdf_file, lsl_config):
    """Loads a xdf file and extracts the eeg and marker stream

    Parameters
    ----------
    xdf_file: `str`
        Full path of xdf file.
    lsl_config: `dict`
        LSL-configuration.

    Returns
    -------
    stream1: `dict`
        The eeg stream.
    stream2: `dict`
        The marker stream.
    """

    streams, fileheader = pyxdf.load_xdf(xdf_file)
    streams_info = []

    for stream in streams:
        streams_info.append(stream['info']['name'][0])

    streams_info = np.array(streams_info)

    eeg_pos = np.where(streams_info == lsl_config['eeg']['name'])[0][0]
    marker_pos = np.where(streams_info == lsl_config['marker']['name'])[0][0]

    return streams[eeg_pos], streams[marker_pos]


def add_class_labels(stream, marker_stream):
    """Adds another row to the stream. It includes the class labels at the cue positions.

    Parameters
    ----------
    stream: `dict`
        The LSL stream which should be appended.
    marker_stream: `dict`
        Marker stream containing info about the cue times and class labels.

    Returns
    -------
    result: `ndarray`
        Data of stream with class labels in the first row.
    """

    time = stream['time_stamps']
    marker_series = np.array(marker_stream['time_series'])
    cue_times = (marker_stream['time_stamps'])[np.where(marker_series == 'Cue')[0]]

    conditions = marker_series[np.where(np.char.find(marker_series[:, 0], 'Start_of_Trial') == 0)[0]]
    conditions[np.where(conditions == 'Start_of_Trial_l')] = 121
    conditions[np.where(conditions == 'Start_of_Trial_r')] = 122

    cue_positions = np.zeros((np.shape(time)[0], 1), dtype=int)
    for t, c in zip(cue_times, conditions):
        pos = find_nearest_index(time, t)
        cue_positions[pos] = c

    return np.append(cue_positions, stream['time_series'], axis=1)


def find_nearest_index(array, value):
    """Finds the position of the value which is nearest to the input value in the array.

    Parameters
    ----------
    array: `ndarray`
        The array of time stamps.
    value: `float`
        The (nearest) value to find in the array.

    Returns
    -------
    idx: `int`
        The index of the (nearest) value in the array.
    """

    idx = np.searchsorted(array, value, side="right")
    if idx == len(array):
        return idx - 1
    else:
        return idx


def save_to_mat(file_path, identifier, data):
    """Saves data as .mat file. If the file already exists data is appended to it.

    Parameters
    ----------
    file_path: `str`
        Path of the .mat file.
    identifier: `str`
        How the data is called in the .mat file.
    data: `ndarray`
        The data to be saved.
    """

    # if there is already a messung.mat file new data is appended to it
    if os.path.isfile(file_path):
        print('INFO new data is appended to ', file_path)
        data_old = scipy.io.loadmat(file_path)[identifier]
        data = np.append(data_old, data, axis=0)

    scipy.io.savemat(file_path, {identifier: data})


def xdf_to_mat(config):

    # ------------- Subject specific variables -------------
    motor_mode = config['gui-input-settings']['motor-mode']
    dimension = config['gui-input-settings']['dimension-mode']
    subject_id = config['gui-input-settings']['subject-id']
    session = str(config['gui-input-settings']['n-session'])
    run = str(config['gui-input-settings']['n-run'])
    # ------------------------------------------------------

    cwd = os.getcwd()
    root_dir = cwd + '/SubjectData/'


    file_name = subject_id + '_run' + run + '_' + motor_mode + '_' + dimension
    xdf_file_path = root_dir + subject_id + '-ses' + session + '/' + file_name + '.xdf'
    mat_file_path = root_dir + subject_id + '-ses' + session + '/' + file_name + '.mat'

    if os.path.exists(mat_file_path):
        print(".mat file for this configuration already exists.")

    else:
        if not os.path.exists(xdf_file_path):
            print(".xdf file for this configuration does not exist.")
            os.makedirs(root_dir + subject_id + '-ses' + session + '/')

        # Extract the eeg and marker lsl stream from the xdf file
        stream_eeg, stream_marker = load_xdf(xdf_file_path, config['general-settings']['lsl-streams'])

        # Add a row to the eeg data for the class labels
        eeg_and_label = add_class_labels(stream_eeg, stream_marker)

        save_to_mat(mat_file_path, 'data', eeg_and_label)
        print('.mat created')


def xdf_to_mat_new(config, path):

    # ------------- Subject specific variables -------------
    motor_mode = config['gui-input-settings']['motor-mode']
    dimension = config['gui-input-settings']['dimension-mode']
    subject_id = config['gui-input-settings']['subject-id']
    session = str(config['gui-input-settings']['n-session'])
    run = str(config['gui-input-settings']['n-run'])
    # ------------------------------------------------------

    file_name = subject_id + '_run' + run + '_' + motor_mode + '_' + dimension
    xdf_file_path = path + subject_id + '-ses' + session + '/' + file_name + '.xdf'
    mat_file_path = path + subject_id + '-ses' + session + '/' + file_name + '.mat'

    if os.path.exists(mat_file_path):
        print(mat_file_path + " already exists.")

    else:
        if not os.path.exists(xdf_file_path):
            print(xdf_file_path + " does not exist.")
            os.makedirs(path + subject_id + '-ses' + session + '/')

        try:
            # Extract the eeg and marker lsl stream from the xdf file
            stream_eeg, stream_marker = load_xdf(xdf_file_path, config['general-settings']['lsl-streams'])

             # Add a row to the eeg data for the class labels
            eeg_and_label = add_class_labels(stream_eeg, stream_marker)

            save_to_mat(mat_file_path, 'data', eeg_and_label)
            print(mat_file_path + ' created.')
        except:
            # Sometimes .xdf file has an invalid footer and cannot be handled the same way as other .xdf files
            print('ERROR: Could not save ' + mat_file_path)
