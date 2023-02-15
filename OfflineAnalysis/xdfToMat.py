# ----------------------------------------------------------------------------------------------------------------------
# Import xdf files and export to mat files
# ----------------------------------------------------------------------------------------------------------------------
import json
import numpy as np
import os
import pyxdf
import scipy.io


def load_xdf(feedback=False):
    streams, fileheader = pyxdf.load_xdf(xdf_file_path)
    streams_info = []

    for stream in streams:
        streams_info.append(stream['info']['name'][0])

    streams_info = np.array(streams_info)

    lsl_config = config['general-settings']['lsl-streams']

    eeg_pos = np.where(streams_info == lsl_config['eeg']['name'])[0][0]
    marker_pos = np.where(streams_info == lsl_config['marker']['name'])[0][0]

    if mode == 'ONLINE' or not feedback:
        return streams[eeg_pos], streams[marker_pos]
    elif mode == 'OFFLINE' and feedback:
        erds_pos = np.where(streams_info == lsl_config['fb-erds']['name'])[0][0]
        lda_pos = np.where(streams_info == lsl_config['fb-lda']['name'])[0][0]
        return streams[eeg_pos], streams[marker_pos], streams[erds_pos], streams[lda_pos]


def add_class_labels(stream):
    time = stream['time_stamps']
    marker_series = np.array(stream_marker['time_series'])
    cue_times = (stream_marker['time_stamps'])[np.where(marker_series == 'Cue')[0]]

    conditions = marker_series[np.where(np.char.find(marker_series[:, 0], 'Start_of_Trial') == 0)[0]]
    conditions[np.where(conditions == 'Start_of_Trial_l')] = 121
    conditions[np.where(conditions == 'Start_of_Trial_r')] = 122

    cue_positions = np.zeros((np.shape(time)[0], 1), dtype=int)
    for t, c in zip(cue_times, conditions):
        pos = find_nearest_index(time, t)
        cue_positions[pos] = c

    return np.append(cue_positions, stream['time_series'], axis=1)


def find_nearest_index(array, value):
    idx = np.searchsorted(array, value, side="right")
    if idx == len(array):
        return idx - 1
    else:
        return idx


def save_to_mat(file_path, identifier, data):
    if os.path.isfile(file_path):
        print(file_path, ' append data')
        data_old = scipy.io.loadmat(file_path)[identifier]
        data = np.append(data_old, data, axis=0)

    scipy.io.savemat(file_path, {identifier: data})


if __name__ == "__main__":

    mode = 'OFFLINE'

    modality = 'ME'
    subject_nr = '3'
    subject_id = 'sub-P00' + subject_nr
    run = '3'

    is_feedback = True
    if run == '1':
        is_feedback = False

    cwd = os.getcwd()

    if mode == 'ONLINE':
        root_dir = cwd + '/data/current/'
        out_dir = root_dir + subject_id + '/' + modality

        # file_name = subject_id + '_' + session + '_task-Default_' + run + '_eeg.xdf'
        # xdf_file_path = root_dir + subject_id + '/' + session + '/eeg/' + file_name

        file_name = '/subj_' + subject_nr + '_block' + run + '.xdf'
        xdf_file_path = root_dir + subject_id + file_name
        mat_file_path = out_dir + '/messung.mat'

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        # Read BCI Configuration
        config_file = cwd + '/../bci-config.json'
        with open(config_file) as json_file:
            config = json.load(json_file)

        # Read XDF and save as mat
        stream_eeg, stream_marker = load_xdf()
        eeg_and_label = add_class_labels(stream_eeg)
        save_to_mat(mat_file_path, 'data', eeg_and_label)

    elif mode == 'OFFLINE':

        root_dir = cwd + '/DataDiana/'
        out_dir = root_dir + subject_id + '/' + modality + '/data'

        # file_name = subject_id + '_' + session + '_task-Default_' + run + '_eeg.xdf'
        # xdf_file_path = root_dir + subject_id + '/' + session + '/eeg/' + file_name

        file_name = 'subj_' + subject_nr + '_block' + run + '.xdf'
        xdf_file_path = root_dir + subject_id + '/' + modality + '/' + file_name

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        config_file = root_dir + subject_id + '/bci-config.json'
        with open(config_file) as json_file:
            config = json.load(json_file)

        # Read XDF and save as mat
        if is_feedback:
            stream_eeg, stream_marker, stream_erds, stream_lda = load_xdf(is_feedback)

            erds_with_labels = add_class_labels(stream_erds)
            lda_with_labels = add_class_labels(stream_lda)
            save_to_mat(out_dir+'/erds_block'+run+'.mat', 'erds', erds_with_labels)
            save_to_mat(out_dir+'/lda_block'+run+'.mat', 'lda', lda_with_labels)
        else:
            stream_eeg, stream_marker = load_xdf(is_feedback)

        eeg_with_labels = add_class_labels(stream_eeg)
        save_to_mat(out_dir+'/eeg_block'+run+'.mat', 'eeg',  eeg_with_labels)

