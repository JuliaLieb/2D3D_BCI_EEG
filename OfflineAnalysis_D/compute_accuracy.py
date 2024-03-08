import json
import numpy as np
import os
import scipy.io
import glob
import matplotlib.pyplot as plt


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
        # plt.plot(epoch[0, :] == cl)
        # plt.show()

    data_nd = np.zeros((len(data), np.shape(data[0])[0], n_samples_task))
    data_nd[:] = None

    # list to np array
    i = 0
    for e in data:
        data_nd[i, :, 0:np.shape(e)[1]] = e
        i += 1

    acc_per_sample = np.zeros((len(data), n_samples_task))
    for i in range(n_samples_task):
        acc_per_sample[:, i] = data_nd[:,0, i] == class_labels

    tst = np.sum(acc_per_sample, axis=0) / len(data)
    plt.plot(tst)
    plt.ylim(0, 1)
    plt.axhline(0.5, linewidth=1, color="black", linestyle=":")
    plt.show()

    return np.mean(acc_per_trial)


if __name__ == "__main__":
    cwd = os.getcwd()
    #root_dir = cwd + '/../../pilot-study/'
    root_dir = 'C:/2D3D_BCI_EEG/SubjectData/'

    # modalities = ['ME', 'MI']
    modalities = ['ME']
    subject_nr = '5'
    subject_id = 'S5'

    #config_file = root_dir + subject_id + '/bci-config.json'
    config_file = 'C:/2D3D_BCI_EEG/SubjectData/S5/CONFIG_S5_ses1_run1_ME_2D.json'

    with open(config_file) as json_file:
        config = json.load(json_file)

    sample_rate = config['eeg-settings']['sample-rate']
    duration_cue = config['general-settings']['timing']['duration-cue']
    duration_task = config['general-settings']['timing']['duration-task']
    n_cue = int(np.floor(sample_rate * duration_cue))
    n_samples_task = int(np.floor(sample_rate * duration_task))

    for modality in modalities:
        print('Modality ' + modality)
        #directory = root_dir + subject_id + '/' + modality + '/data'
        directory ='C:/2D3D_BCI_EEG/SubjectData/S5/data'
        my_files = glob.glob(directory + '/lda_*.mat')
        for f in my_files:
            data_lda = scipy.io.loadmat(f)['lda'].T
            data_lda, labels = extract_epochs(data_lda, n_samples_task)
            accuracy = compute_accuracy(data_lda, labels)
            print('     Accuracy %: ', accuracy*100)

