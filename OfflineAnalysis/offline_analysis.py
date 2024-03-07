# ----------------------------------------------------------------------------------------------------------------------
# Offline analysis of recorded eeg data
# ----------------------------------------------------------------------------------------------------------------------
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import mne
from mne.time_frequency import tfr_multitaper
from mne.stats import permutation_cluster_1samp_test as pcluster_test
import os
import scipy.io


def extract_epochs(data):
    data_labels = data[0, :]
    data = data[1:, :]
    indexes = np.where((data_labels == 121) | (data_labels == 122))[0]

    epochs = []
    for idx in indexes:
        epochs.append(data[:, idx:idx + n_samples_task])

    return epochs


def show_lda_plots(data):
    time = [0, config['general-settings']['timing']['duration-cue'] + config['general-settings']['timing'][
        'duration-task']]
    step = (config['general-settings']['timing']['duration-cue'] + config['general-settings']['timing'][
        'duration-task']) / n_samples_task
    time_series = np.arange(start=time[0], stop=time[1], step=step)
    class_label = np.zeros_like(time_series)
    for epoch in data:
        class_label[:] = epoch[0, 0] - 120
        plt.clf()
        samples = np.shape(epoch[1, :])[0]
        plt.plot(time_series[0:samples], class_label[0:samples], 'k')
        plt.plot(time_series[0:samples], epoch[1, 0:samples] + 1, 'b')
        plt.show()


def show_erds_plots(data):
    time = [0, config['general-settings']['timing']['duration-cue'] + config['general-settings']['timing'][
        'duration-task']]
    step = (config['general-settings']['timing']['duration-cue'] + config['general-settings']['timing'][
        'duration-task']) / n_samples_task
    nr_roi, samples = np.shape(data[0])
    data_nd = np.zeros((len(data), nr_roi, samples))
    data_nd[:] = None

    # list to np array
    cnt = 0
    for epoch in data:
        data_nd[cnt, :, 0:np.shape(epoch)[1]] = epoch
        cnt += 1

    idx_1 = np.where(class_labels == 0)[0]
    idx_2 = np.where(class_labels == 1)[0]

    # remove short trials (nan values)
    for val in np.unique(np.where(np.isnan(data_nd))[0]):
        idx_1 = np.delete(idx_1, np.argwhere(idx_1 == val))
        idx_2 = np.delete(idx_2, np.argwhere(idx_2 == val))

    # average erds values for all trials
    erds_mean_cl1 = np.mean(data_nd[idx_1], axis=0)
    erds_mean_cl2 = np.mean(data_nd[idx_2], axis=0)
    time_series = np.arange(start=time[0], stop=time[1], step=step)

    # new_samples = int(samples/3)
    # erds_mean_cl1 = signal.resample(erds_mean_cl1, new_samples, axis=1)
    # erds_mean_cl2 = signal.resample(erds_mean_cl2, new_samples, axis=1)
    # time_series = np.arange(start=time[0], stop=time[1], step=(config['general-settings']['timing']['duration-cue']+config['general-settings']['timing']['duration-task'])/new_samples)

    fig, axs = plt.subplots(3, 2)
    axs[0, 0].plot(time_series, erds_mean_cl1[0, :])
    axs[0, 0].set_title('ROI 1')
    axs[0, 1].plot(time_series, erds_mean_cl1[1, :])
    axs[0, 1].set_title('ROI 2')
    axs[1, 0].plot(time_series, erds_mean_cl1[2, :])
    axs[1, 0].set_title('ROI 3')
    axs[1, 1].plot(time_series, erds_mean_cl1[3, :])
    axs[1, 1].set_title('ROI 4')
    axs[2, 0].plot(time_series, erds_mean_cl1[4, :])
    axs[2, 0].set_title('ROI 5')
    axs[2, 1].plot(time_series, erds_mean_cl1[5, :])
    axs[2, 1].set_title('ROI 6')
    fig.suptitle('Mean ERDS Class 1')
    plt.show()

    fig2, axs2 = plt.subplots(3, 2)
    axs2[0, 0].plot(time_series, erds_mean_cl2[0, :])
    axs2[0, 0].set_title('ROI 1')
    axs2[0, 1].plot(time_series, erds_mean_cl2[1, :])
    axs2[0, 1].set_title('ROI 2')
    axs2[1, 0].plot(time_series, erds_mean_cl2[2, :])
    axs2[1, 0].set_title('ROI 3')
    axs2[1, 1].plot(time_series, erds_mean_cl2[3, :])
    axs2[1, 1].set_title('ROI 4')
    axs2[2, 0].plot(time_series, erds_mean_cl2[4, :])
    axs2[2, 0].set_title('ROI 5')
    axs2[2, 1].plot(time_series, erds_mean_cl2[5, :])
    axs2[2, 1].set_title('ROI 6')
    fig2.suptitle('Mean ERDS Class 2')
    plt.show()


def compute_accuracy(data, median=False):
    samples_accurate = 0
    samples_total = 0

    if median:
        for epoch, cl in zip(data, class_labels):
            if np.median(epoch[0, :]) == cl:
                samples_accurate += 1
            samples_total += 1

    else:
        for epoch, cl in zip(data, class_labels):
            samples_accurate += len(np.where(epoch[0, :] == cl)[0])
            samples_total += len(epoch[0, :])

    return samples_accurate / samples_total


def analyze_eeg(eeg):
    ch_names = []
    bads = []
    for name in config['eeg-settings']['channels']:
        ch_names.append(name)
        if config['eeg-settings']['channels'][name]['enabled'] is False:
            bads.append(name)

    n_ch = len(ch_names)
    info = mne.create_info(ch_names=ch_names, sfreq=sample_rate, ch_types=['misc'] * n_ch)
    info['bads'] = bads
    print(info)

    # # Display raw data
    # for i in range(len(indexes_class_all)):
    #     raw = mne.io.RawArray(eeg[1:n_ch+1, indexes_class_all[i]-n_ref:indexes_class_all[i]+n_samples_trial], info)
    #     raw.plot(show_scrollbars=True, show_scalebars=True, block=True)

    raw = mne.io.RawArray(eeg[1:n_ch + 1, :], info)

    event_dict = dict(left=0, right=1)
    # picks = ['C3', 'Cz', 'C4']
    # picks = ['F3', 'F4', 'C3', 'C4', 'P3', 'P4']

    # picks = ['F3', 'F4']
    # picks = ['C3', 'C4']
    picks = ['P3', 'P4']

    # eeg = extract_eeg_epochs(eeg, n_ch)
    # n_ep, n_ch, n_s = np.shape(eeg)
    # events_array = np.column_stack((np.arange(0, n_ep*n_s, n_s), np.zeros(n_ep, dtype=int), np.array(class_labels, dtype=int)))
    # eeg_epochs_array = mne.EpochsArray(eeg, info, tmin=-config['general-settings']['timing']['duration-ref'], events=events_array, event_id=event_dict)
    # eeg_epochs_array.plot(picks=picks, show_scrollbars=False, events=events_array, event_id=event_dict, n_epochs=5)

    tmin = -duration_ref
    tmax = duration_task
    events = np.column_stack(
        (indexes_class_all, np.zeros(len(indexes_class_all), dtype=int), np.array(class_labels, dtype=int)))
    epochs = mne.Epochs(raw, events, event_dict, tmin - 0.5, tmax + 0.5, picks=picks, baseline=None, preload=True)
    # epochs.plot(picks=picks, show_scrollbars=True, events=events, event_id=event_dict)

    # freqs = np.arange(2, 31)  # frequencies from 2-30Hz
    freqs = np.arange(1, 30)
    vmin, vmax = -1, 1  # set min and max ERDS values in plot
    # baseline = [tmin, -0.5]  # baseline interval (in s)
    baseline = [tmin, 0]  # baseline interval (in s)
    cnorm = TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)  # min, center, and max ERDS
    kwargs = dict(n_permutations=100, step_down_p=0.05, seed=1,
                  buffer_size=None, out_type='mask')  # for cluster test

    tfr = tfr_multitaper(epochs, picks=picks, freqs=freqs, n_cycles=freqs, use_fft=True, return_itc=False,
                         average=False, decim=2)
    tfr.crop(tmin, tmax).apply_baseline(baseline,
                                        mode="percent")  # subtracting the mean of baseline values followed by dividing by the mean of baseline values (‘percent’)
    tfr.crop(0, tmax)

    for event in event_dict:
        # select desired epochs for visualization
        tfr_ev = tfr[event]
        fig, axes = plt.subplots(1, 3, figsize=(12, 4), gridspec_kw={"width_ratios": [10, 10, 0.5]}) # , 0.5
        axes = axes.flatten()
        for ch, ax in enumerate(axes[:-1]):  # for each channel  axes[:-1]
            # # positive clusters
            # _, c1, p1, _ = pcluster_test(tfr_ev.data[:, ch], tail=1, **kwargs)
            # # negative clusters
            # _, c2, p2, _ = pcluster_test(tfr_ev.data[:, ch], tail=-1, **kwargs)
            #
            # # note that we keep clusters with p <= 0.05 from the combined clusters
            # # of two independent tests; in this example, we do not correct for
            # # these two comparisons
            # c = np.stack(c1 + c2, axis=2)  # combined clusters
            # p = np.concatenate((p1, p2))  # combined p-values
            # mask = c[..., p <= 0.5].any(axis=-1)  # 0.05

            # plot TFR (ERDS map with masking)
            tfr_ev.average().plot([ch], cmap="RdBu", cnorm=cnorm, axes=ax,
                                  colorbar=False, show=False, vmin=-1.5, vmax=1.5)  #, mask=mask,
                                  # mask_style="mask")

            ax.set_title(epochs.ch_names[ch], fontsize=10)
            ax.axvline(0, linewidth=1, color="black", linestyle=":")  # event
            if ch != 0:
                ax.set_ylabel("")
                ax.set_yticklabels("")

        fig.colorbar(axes[0].images[-1], cax=axes[-1])
        fig.suptitle(f"ERDS - {event} hand")

        plt.savefig('{}/erds_{}_{}_{}_{}{}.png'.format(dir_plots, modality, str(run), event, picks[0], picks[1]), format='png')
        plt.show()

    return eeg


if __name__ == "__main__":
    cwd = os.getcwd()
    #root_dir = cwd + './SubjectData/S5/'
    #root_dir = cwd + './SubjectData/S5/'

    #modalities = ['ME', 'MI']
    modalities = ['ME']
    subject_id = 'S5'

    dir_plots = 'C:/2D3D_BCI_EEG/SubjectData/S5/plots/erds_eeg'
    if not os.path.exists(dir_plots):
        os.makedirs(dir_plots)

    config_file = 'C:/2D3D_BCI_EEG/SubjectData/S5/CONFIG_S5_ses1_run2_ME_2D.json'
    # if modality == 'ME' and (run == '1' or run == '2'):
    #     config_file = root_dir + subject_id + '/bci-config_run1_run2.json'

    #with open(config_file) as json_file:
    #    config = json.load(json_file)
    with open(config_file) as json_file:
        config = json.load(json_file)

    sample_rate = config['eeg-settings']['sample-rate']
    duration_ref = config['general-settings']['timing']['duration-ref']
    duration_cue = config['general-settings']['timing']['duration-cue']

    n_ref = int(np.floor(sample_rate * duration_ref))

    for modality in modalities:
        directory = 'C:/2D3D_BCI_EEG/SubjectData/S5/data'

        for run in range(1, 4):
            f_name = directory + '/eeg_block'+str(run)+'.mat'
            if not os.path.exists(f_name):
                continue
            # LOAD MAT FILES
            data_eeg = scipy.io.loadmat(f_name)['eeg'].T
            data_erds = scipy.io.loadmat(directory + '/erds_block'+run+'.mat')['erds'].T
            data_lda = scipy.io.loadmat(directory + '/lda_block'+run+'.mat')['lda'].T
            #
            # EXTRACT EPOCHS

            duration_task = duration_cue + config['general-settings']['timing']['duration-task']
            if subject_id == 'sub-P002' and modality == 'ME' and (run == 1 or run == 2):
                duration_task = duration_cue + 3.75

            n_samples_task = int(np.floor(sample_rate * duration_task))
            n_samples_trial = n_ref + n_samples_task

            indexes_class_1 = np.where(data_eeg[0, :] == 121)[0]
            indexes_class_2 = np.where(data_eeg[0, :] == 122)[0]
            indexes_class_all = np.sort(np.append(indexes_class_1, indexes_class_2), axis=0)

            n_trials = len(indexes_class_all)
            class_labels = data_eeg[0, indexes_class_all] - 121

            # COMPUTE ERDS MAP FROM EEG SIGNAL
            data_eeg = analyze_eeg(data_eeg)

