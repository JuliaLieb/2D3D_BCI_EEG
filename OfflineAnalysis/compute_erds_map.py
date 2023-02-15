import matplotlib.pyplot as plt
import json
import numpy as np
import os
import scipy.io
import glob


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


def plot_erds(data, title, s_rate, mod, erds_mode, cl):

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

    create_subplot(figure, axs[0, 0], data[0, :], extent, 'ROI1', xtick_labels)
    create_subplot(figure, axs[0, 1], data[1, :], extent, 'ROI2', xtick_labels)
    create_subplot(figure, axs[1, 0], data[2, :], extent, 'ROI3', xtick_labels)
    create_subplot(figure, axs[1, 1], data[3, :], extent, 'ROI4', xtick_labels)
    create_subplot(figure, axs[2, 0], data[4, :], extent, 'ROI5', xtick_labels)
    create_subplot(figure, axs[2, 1], data[5, :], extent, 'ROI6', xtick_labels)

    figure.colorbar(axs[0][1].images[-1], cax=axs[0][-1])
    figure.colorbar(axs[1][1].images[-1], cax=axs[1][-1])
    figure.colorbar(axs[2][1].images[-1], cax=axs[2][-1])

    figure.suptitle(title)
    plt.savefig('{}/erds_{}_{}_{}.png'.format(dir_plots, mod, erds_mode, cl), format='png')
    plt.show()


if __name__ == "__main__":
    cwd = os.getcwd()
    root_dir = cwd + '/DataDiana/'

    modalities = ['ME', 'MI']
    subject_nr = '3'
    subject_id = 'sub-P00' + subject_nr

    config_file = root_dir + subject_id + '/bci-config.json'

    with open(config_file) as json_file:
        config = json.load(json_file)

    sample_rate = config['eeg-settings']['sample-rate']
    duration_ref = config['general-settings']['timing']['duration-ref']
    duration_cue = config['general-settings']['timing']['duration-cue']
    duration_task = config['general-settings']['timing']['duration-task']
    n_cue = int(np.floor(sample_rate * duration_cue))
    n_ref = int(np.floor(sample_rate * duration_ref))
    n_samples_task = n_cue + int(np.floor(sample_rate * duration_task))
    n_samples_task_org = n_samples_task
    n_samples_trial = n_ref + n_cue + n_samples_task

    for modality in modalities:
        print('Modality ' + modality)
        directory = root_dir + subject_id + '/' + modality + '/data'
        dir_plots = root_dir + subject_id + '/plots/erds_fb'
        my_files = glob.glob(directory + '/erds_*.mat')

        if not os.path.exists(dir_plots):
            os.makedirs(dir_plots)

        cnt = 0
        for f in my_files:
            data_erds = scipy.io.loadmat(f)['erds'].T

            if subject_nr == 2 and modality == 'ME' and 'block2' in f:
                n_samples_task = int(np.floor(sample_rate * 5))
            else:
                n_samples_task = n_samples_task_org

            data_epoched, n_samples, labels = extract_epochs(data_erds, n_samples_task)
            data_1 = data_epoched[np.where(labels == 0)[0]]
            data_2 = data_epoched[np.where(labels == 1)[0]]

            if 'block2' in f:
                mode = 'average'
            elif 'block3' in f:
                mode = 'single'
            else:
                mode = 'nan'

            plot_erds(np.mean(data_1, axis=0), 'ERDS - left hand', sample_rate, modality, mode, 'l')
            plot_erds(np.mean(data_2, axis=0), 'ERDS - right hand', sample_rate, modality, mode, 'r')

