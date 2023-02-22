
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

    root_dir = cwd + '/SubjectData/' + subject_id
    out_dir = root_dir + '/data'
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    xdf_file_name = subject_id + '_ses' + str(session) + '_run' + str(run) + '_' + motor_mode + '_' + dimension + '.xdf'
    xdf_file_path = root_dir + '/' + xdf_file_name

    # Read XDF and save as mat
    if is_feedback:
        stream_eeg, stream_marker, stream_erds, stream_lda = load_xdf(config, xdf_file_path, is_feedback)

        erds_with_labels = add_class_labels(stream_erds, stream_marker)
        lda_with_labels = add_class_labels(stream_lda, stream_marker)
        save_to_mat(out_dir+'/erds_ses' + session + '_run' + run + '_' + motor_mode + '.mat', 'erds', erds_with_labels)
        save_to_mat(out_dir+'/lda_ses' + session + '_run' + run + '_' + motor_mode + '.mat', 'lda', lda_with_labels)
    else:
        stream_eeg, stream_marker = load_xdf(config, xdf_file_path, is_feedback)

    eeg_with_labels = add_class_labels(stream_eeg, stream_marker)
    save_to_mat(out_dir+'/eeg_ses' + session + '_run' + run + '_' + motor_mode + '.mat', 'eeg',  eeg_with_labels)

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
    motor_mode = config['gui-input-settings']['motor-mode']

    if int(run) == 1:
        print('Session ' + session + ', ' + motor_mode + ', run ' + run + ': training of classifier')
    elif int(run) > 1:
        file = root_dir + subject_id + '/data/' + 'lda_ses' + session + '_run' + run + '_' + motor_mode + '.mat'
        data_lda = scipy.io.loadmat(file)['lda'].T
        data_lda, labels = extract_epochs(data_lda, n_samples_task)
        accuracy = compute_accuracy(data_lda, labels)
        print('Session ' + session + ', ' + motor_mode + ', run ' + run + ': accuracy in %: ', accuracy * 100)

def extract_epochs(data, n):
    cue_indexes = np.where(data[0, :] != 0)[0]
    cl_labels = np.array(data[0, cue_indexes]-121, dtype=int)
    data = data[1:, :]
    epochs = []
    min_length = n
    n_trials = len(cue_indexes)

    for i in range(n_trials):
        idx1 = cue_indexes[i]
        idx2 = idx1 + n
        if i < n_trials-1 and idx2 > cue_indexes[i+1]:
            idx2 = cue_indexes[i+1]
        epochs.append(data[:, idx1:idx2])
        min_length = np.min([min_length, idx2-idx1])

    data_nd = np.zeros((len(epochs), np.shape(data)[0], min_length))
    data_nd[:] = None

    # list to np array
    i = 0
    for e in epochs:
        data_nd[i, :, :] = e[:, 0:min_length]
        i += 1

    return data_nd, min_length, cl_labels


def plot_erds(data, title, s_rate, session, run, motor_mode, cl, n_cue, dir_plots):

    def create_subplot(fig, ax, y, ext, subtitle, xtick_l):

        y = np.append(data_fill, y, axis=0)
        im = ax.imshow(y[np.newaxis, :], vmin=-1.5, vmax=1.5, cmap="RdBu", aspect="auto", extent=ext)
        ax.set_yticks([])
        ax.set_xlim(ext[0], ext[1])
        ax.set_xticklabels(xtick_l)
        # ax.axvline(n_ref, linewidth=1, color="black", linestyle=":")
        # fig.colorbar(im, ax=ax)
        ax.set_title(subtitle)

    data_fill = np.zeros((n_cue,))
    x = np.arange(0, np.shape(data)[1] + n_cue, 1)
    extent = [x[0]-(x[1]-x[0])/2., x[-1]+(x[1]-x[0])/2., 0, 1]

    figure, axs = plt.subplots(3, 3, figsize=(15, 10), gridspec_kw={"width_ratios": [10, 10, 0.5]})
    step = s_rate/2
    xtick_labels = np.arange(-step, int(np.shape(x)[0]), step) / s_rate
    if len(xtick_labels) > 10:
        step = s_rate
        xtick_labels = np.arange(-step, int(np.shape(x)[0]), step) / s_rate

    # if len(xtick_labels) > 9:
    #     step = s_rate*2
    #     xtick_labels = np.arange(-step, int(np.shape(x)[0]), step) / s_rate

    xtick_labels = np.array(xtick_labels, dtype=str)
    xtick_labels[-1] = xtick_labels[-1] + ' s'

    create_subplot(figure, axs[0, 0], data[0, :], extent, 'F3', xtick_labels)
    create_subplot(figure, axs[0, 1], data[1, :], extent, 'F4', xtick_labels)
    create_subplot(figure, axs[1, 0], data[2, :], extent, 'C3', xtick_labels)
    create_subplot(figure, axs[1, 1], data[3, :], extent, 'C4', xtick_labels)
    create_subplot(figure, axs[2, 0], data[4, :], extent, 'P3', xtick_labels)
    create_subplot(figure, axs[2, 1], data[5, :], extent, 'P4', xtick_labels)

    figure.colorbar(axs[0][1].images[-1], cax=axs[0][-1])
    figure.colorbar(axs[1][1].images[-1], cax=axs[1][-1])
    figure.colorbar(axs[2][1].images[-1], cax=axs[2][-1])

    figure.suptitle(title)
    plt.savefig('{}/erds_{}_{}_{}_{}.png'.format(dir_plots, session, run, motor_mode, cl), format='png')
    plt.show()

def compute_erds_map(current_config_file):
    with open(current_config_file) as json_file:
        config = json.load(json_file)

    root_dir = cwd + '/SubjectData/'
    sample_rate = config['eeg-settings']['sample-rate']
    duration_ref = config['general-settings']['timing']['duration-ref']
    duration_cue = config['general-settings']['timing']['duration-cue']
    duration_task = config['general-settings']['timing']['duration-task']
    n_cue = int(np.floor(sample_rate * duration_cue))
    n_ref = int(np.floor(sample_rate * duration_ref))
    n_samples_task = n_cue + int(np.floor(sample_rate * duration_task))
    # n_samples_task_org = n_samples_task
    n_samples_trial = n_ref + n_cue + n_samples_task

    subject_id = config['gui-input-settings']['subject-id']
    session = str(config['gui-input-settings']['n-session'])
    run = str(config['gui-input-settings']['n-run'])
    motor_mode = config['gui-input-settings']['motor-mode']

    if int(run) == 1:
        print('Session ' + session + ', ' + motor_mode + ', run ' + run + ': training of classifier')
    elif int(run) > 1:
        current_erds_file = root_dir + subject_id + '/data/erds_ses' + session + '_run' + run + '_' + motor_mode
        dir_plots = root_dir + subject_id + '/plots'
        if not os.path.exists(dir_plots):
            os.makedirs(dir_plots)

        data_erds = scipy.io.loadmat(current_erds_file)['erds'].T

        data_epoched, n_samples, labels = extract_epochs(data_erds, n_samples_task)
        data_1 = data_epoched[np.where(labels == 0)[0]]
        data_2 = data_epoched[np.where(labels == 1)[0]]

        plot_erds(np.mean(data_1, axis=0), 'ERDS - left hand', sample_rate, session, run, motor_mode, 'l', n_cue, dir_plots)
        plot_erds(np.mean(data_2, axis=0), 'ERDS - right hand', sample_rate, session, run, motor_mode, 'r', n_cue, dir_plots)


if __name__ == "__main__":
    cwd = os.getcwd()
    # Read BCI Configuration
    config_file = cwd + '/bci-config.json'
    with open(config_file) as json_file:
        config = json.load(json_file)

    subject_id = config['gui-input-settings']['subject-id']

    root_dir = cwd + '/SubjectData/'


    # convert all .xdf files which have corresponding .json file to .mat
    all_config_files = glob.glob(root_dir + subject_id + '/*.json')
    for current_config_file in all_config_files:
        xdf_to_mat_file(current_config_file, cwd)

    #for all available .json files: calculate accuracy
    for current_config_file in all_config_files:
       calculate_accuracy(current_config_file)

    # for all available .json files: create ERDS plots
    #for current_config_file in all_config_files:
    #    compute_erds_map(current_config_file)



