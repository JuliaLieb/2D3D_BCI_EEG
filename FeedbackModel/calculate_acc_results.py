
import pyxdf
import scipy.io
import json
import numpy as np
import os
import scipy.io
import glob
import matplotlib.pyplot as plt

def load_xdf(config, xdf_file_path, feedback):
    streams, fileheader = pyxdf.load_xdf(xdf_file_path)
    streams_info = []

    for stream in streams:
        streams_info.append(stream['info']['name'][0])

    streams_info = np.array(streams_info)

    lsl_config = config['general-settings']['lsl-streams']

    eeg_pos = np.where(streams_info == lsl_config['eeg']['name'])[0][0]
    marker_pos = np.where(streams_info == lsl_config['marker']['name'])[0][0]


    if not feedback:
        return streams[eeg_pos], streams[marker_pos]
    elif feedback:
        erds_pos = np.where(streams_info == lsl_config['fb-erds']['name'])[0][0]
        lda_pos = np.where(streams_info == lsl_config['fb-lda']['name'])[0][0]
        return streams[eeg_pos], streams[marker_pos], streams[erds_pos], streams[lda_pos]
def add_class_labels(stream, stream_marker):
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


def xdf_to_mat_file(current_config_file, cwd):

    with open(current_config_file) as json_file:
        config = json.load(json_file)
    # ------------- Subject specific variables -------------
    motor_mode = config['gui-input-settings']['motor-mode']
    dimension = config['gui-input-settings']['dimension-mode']
    subject_id = config['gui-input-settings']['subject-id']
    session = str(config['gui-input-settings']['n-session'])
    run = str(config['gui-input-settings']['n-run'])
    # ------------------------------------------------------

    is_feedback = True
    if run == '1':
        is_feedback = False

    root_dir = cwd + '/SubjectData/' + subject_id + '-ses' + str(n_session)
    out_dir = root_dir + '/data'
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    xdf_file_name = subject_id + '_run' + str(run) + '_' + motor_mode + '_' + dimension + '.xdf'
    xdf_file_path = root_dir + '/' + xdf_file_name

    # Read XDF and save as mat
    if is_feedback:
        stream_eeg, stream_marker, stream_erds, stream_lda = load_xdf(config, xdf_file_path, is_feedback)

        erds_with_labels = add_class_labels(stream_erds, stream_marker)
        xdf_file_erds = out_dir+'/erds' + '_run' + run + "_" + motor_mode + '.mat'
        if not os.path.exists(xdf_file_erds):
            save_to_mat(xdf_file_erds, 'erds', erds_with_labels)

        lda_with_labels = add_class_labels(stream_lda, stream_marker)
        xdf_file_lda = out_dir + '/lda' + '_run' + run + "_" + motor_mode + '.mat'
        if not os.path.exists(xdf_file_lda):
            save_to_mat(xdf_file_lda, 'lda', lda_with_labels)
    else:
        stream_eeg, stream_marker = load_xdf(config, xdf_file_path, is_feedback)

    eeg_with_labels = add_class_labels(stream_eeg, stream_marker)
    xdf_file_eeg = out_dir+'/eeg' + '_run' + run + "_" + motor_mode + '.mat'
    if not os.path.exists(xdf_file_eeg):
        save_to_mat(xdf_file_eeg, 'eeg',  eeg_with_labels)

def extract_epochs(data, n_samples):
    data_labels = data[0, :]
    data = data[1:, :]
    indexes = np.where((data_labels == 121) | (data_labels == 122))[0]

    epochs = []
    n_trials = len(indexes)
    for i in range(n_trials):
        idx1 = indexes[i]
        idx2 = idx1 + n_samples
        if i < n_trials-1 and idx2 > indexes[i+1]:
            idx2 = indexes[i+1]
        epochs.append(data[:, idx1:idx2])

    return epochs, np.array(data_labels[indexes] - 121, dtype=int)

def compute_accuracy(data, class_labels):

    acc_per_trial = []

    for epoch, cl in zip(data, class_labels):
        acc_per_trial.append(np.sum(epoch[0, :] == cl) / len(epoch[0, :]))

    return np.mean(acc_per_trial)

def calculate_accuracy(current_config_file):

    with open(current_config_file) as json_file:
        config = json.load(json_file)

    sample_rate = config['eeg-settings']['sample-rate']
    duration_task = config['general-settings']['timing']['duration-task']
    n_samples_task = int(np.floor(sample_rate * duration_task))

    subject_id = config['gui-input-settings']['subject-id']
    session = str(config['gui-input-settings']['n-session'])
    run = str(config['gui-input-settings']['n-run'])
    motor_mode = str(config['gui-input-settings']['motor-mode'])

    # for modality in modalities:
    #if int(run) == 1:
        # print("1st run only for training of classifier - no accuracy can be computed.")
    if not int(run) == 1:
        file = root_dir + subject_id + '-ses' + str(n_session) + '/data/' + 'lda' + '_run' + run + "_" + motor_mode + '.mat'
        data_lda = scipy.io.loadmat(file)['lda'].T
        data_lda, labels = extract_epochs(data_lda, n_samples_task)
        accuracy = compute_accuracy(data_lda, labels)
        print(motor_mode + ' Run ' + run + ': accuracy in %: ', accuracy * 100)

if __name__ == "__main__":
    cwd = os.getcwd()
    # Read BCI Configuration
    config_file = cwd + '/bci-config.json'
    with open(config_file) as json_file:
        config = json.load(json_file)

    subject_id = config['gui-input-settings']['subject-id']
    n_session = config['gui-input-settings']['n-session']

    root_dir = cwd + '/SubjectData/'

    # convert all .xdf files which have corresponding .json file to .mat
    all_config_files = glob.glob(root_dir + subject_id + '-ses' + str(n_session) + '/*.json')
    for current_config_file in all_config_files:
        xdf_to_mat_file(current_config_file, cwd)

    # for all available .json files: calculate accuracy
    for current_config_file in all_config_files:
        calculate_accuracy(current_config_file)

