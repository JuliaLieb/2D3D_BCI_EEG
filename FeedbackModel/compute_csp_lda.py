"""
Calculates common spatial pattern (CSP) filters and linear discriminant analysis (LDA) coefficients from eeg data.
The output is saved as CSP.mat and LDA.mat and needed as input for the feedback model (feedback_model.py).
"""
import json
import numpy as np
import os
import scipy.io
from scipy import signal, linalg

import xdf_to_mat


class CSPAndLDA:
    """Provides methods the for calculation of common spatial pattern (CSP) and linear discriminant analysis (LDA)
    coefficients from eeg data

    Parameters
    ----------
    eeg: `ndarray`
        2-D array with EEG data (channels, time series).
    labels: `ndarray`
        1-D array with class labels at cue time.
    bci_config: `dict`
        All settings for the feedback model and analysis.

    Other Parameters
    ----------------
    n_channels: `int`
        Number of eeg channels.
    pos_class_1: `ndarray`
        Indexes for all class 1 labels (1-D array).
    pos_class_2: `ndarray`
        Indexes for all class 2 labels (1-D array).
    n_trials: `int`
        Number of trials.
    sample_rate: `int`
        Sample rate of the eeg signal.
    channel_settings: `dict`
        Settings for the eeg channels (index, mapping to ROI, enabled).
    bp_frequency: `list`
        Pass frequencies for the bandpass filter.
    bp_order: `int`
        Order of the bandpass.
    d_cue: `float`
        Duration of the cue time.
    d_task: `float`
        Duration of the task.
    """

    def __init__(self, eeg, labels, bci_config):
        self.eeg = eeg
        self.labels = labels
        self.n_channels = None
        self.pos_class_1 = np.where(self.labels == 121)[0]
        self.pos_class_2 = np.where(self.labels == 122)[0]
        self.n_trials = [len(self.pos_class_1), len(self.pos_class_2)]
        self.sample_rate = bci_config['eeg-settings']['sample-rate']
        self.channel_settings = bci_config['eeg-settings']['channels']

        self.bp_frequency = bci_config['feedback-model-settings']['bandpass']['fpass']
        self.bp_order = bci_config['feedback-model-settings']['bandpass']['order-offline']

        self.d_cue = bci_config['general-settings']['timing']['duration-cue']
        self.d_task = bci_config['general-settings']['timing']['duration-task']

        self.__select_channels()
        self.__bandpass()

    def __select_channels(self):
        """Removes eeg channels which are not used in further computation.
        """

        list_is_channel_enabled = np.zeros((np.shape(self.eeg)[0],), dtype=bool)

        cnt = 0
        for ch in self.channel_settings:
            obj = self.channel_settings[ch]
            list_is_channel_enabled[cnt] = obj['enabled']
            cnt += 1

        self.eeg = self.eeg[np.where(list_is_channel_enabled)[0]]
        self.n_channels = np.shape(self.eeg)[0]

    def __extract_epochs(self):
        """Extracts epochs from the eeg data for both classes.

        Returns
        -------
        class_1: `ndarray`
            Epochs of class 1 trials.
        class_2: `ndarray`
            Epochs of class 2 trials.
        """

        n_cue = int(np.floor(self.sample_rate * self.d_cue))
        n_samples = n_cue + int(np.floor(self.sample_rate * self.d_task))
        class_1, class_2 = np.array([]), np.array([])

        for i in range(self.n_trials[0]):
            if i == 0:
                class_1 = self.eeg[:, self.pos_class_1[i] + n_cue:self.pos_class_1[i] + n_samples]
            else:
                class_1 = np.append(class_1, self.eeg[:, self.pos_class_1[i] + n_cue:self.pos_class_1[i] + n_samples],
                                    axis=1)

        for i in range(self.n_trials[1]):
            if i == 0:
                class_2 = self.eeg[:, self.pos_class_2[i] + n_cue:self.pos_class_2[i] + n_samples]
            else:
                class_2 = np.append(class_2, self.eeg[:, self.pos_class_2[i] + n_cue:self.pos_class_2[i] + n_samples],
                                    axis=1)
        return class_1, class_2

    def __bandpass(self):
        """Bandpass filters the eeg data.
        """

        self.eeg[np.isnan(self.eeg)] = 0
        [b, a] = signal.butter(self.bp_order, np.divide(self.bp_frequency, self.sample_rate / 2), 'bandpass', False)
        self.eeg = signal.filtfilt(b, a, self.eeg, padtype='odd', padlen=3 * (max(len(b), len(a)) - 1), axis=1)

    def compute_csp(self):
        """Computes CSP filters.

        Returns
        -------
        csp_filter: `ndarray`
            CSP filters (2-D array).
        """

        n_filters = 2  # defines how many virtual CSP channels are used

        # extract relevant epochs for each class
        data_1, data_2 = self.__extract_epochs()

        eigen_vectors = self.train_csp(data_1, data_2)

        # select csp filter
        selected_filter = np.ones(self.n_channels, dtype=bool)
        selected_filter[n_filters:len(selected_filter) - n_filters] = False

        return eigen_vectors[:, selected_filter].T

    def compute_lda(self, csp_filter):
        """Computes LDA coefficients.

        Parameters
        ----------
        csp_filter: `ndarray`
            CSP filter (2-D array).

        Returns
        -------
        lda_coefficients: `ndarray`
            LDA coefficients (2-D array).
        """

        # define extraction parameter
        n_samples = int(np.floor(self.sample_rate * 3))
        csp_signal = np.square(np.matmul(csp_filter, self.eeg))

        window_length_seconds = 1
        window_length_samples = int(np.floor(window_length_seconds * self.sample_rate))
        csp_signal = signal.lfilter(np.ones(window_length_samples) / window_length_samples, 1, csp_signal)
        csp_signal = np.log10(csp_signal)

        x_train_1, x_train_2 = [], []
        for i in range(self.n_trials[0]):
            x_train_1.append(csp_signal[:, self.pos_class_1[i] + n_samples])

        for i in range(self.n_trials[1]):
            x_train_2.append(csp_signal[:, self.pos_class_2[i] + n_samples])

        x_train = np.append(np.array(x_train_1), np.array(x_train_2), axis=0)
        y_train = np.append(np.ones(self.n_trials[0], dtype=int), np.ones(self.n_trials[1], dtype=int) * 2)

        return self.train_lda(x_train, y_train)

    @staticmethod
    def train_csp(data_1, data_2):
        """Trains common spatial patterns transformation.

        Parameters
        ----------
        data_1: `ndarray`
            Data of class 1 (2-D array, channels x time-samples).
        data_2: `ndarray`
            Data of class 2 (2-D array, channels x time-samples).

        Returns
        -------
        eigen_vectors: `ndarray`
            CSP weights (2-D array).
        """

        cov_1 = np.cov(data_1)
        cov_2 = np.cov(data_2)
        norm_cov_1 = cov_1 / np.trace(cov_1)
        norm_cov_2 = cov_2 / np.trace(cov_2)

        # solve generalized eigenvalue problem and normalize
        eigen_values, eigen_vectors = scipy.linalg.eig(a=norm_cov_1, b=norm_cov_1 + norm_cov_2, left=True, right=False)
        eigen_vectors = eigen_vectors / np.max(np.abs(eigen_vectors), axis=0)

        # sort eigenvectors in descending order of the eigenvalues
        idx = eigen_values.argsort()[::-1]
        eigen_vectors = eigen_vectors[:, idx]
        return eigen_vectors

    @staticmethod
    def train_lda(data_train, classlabels, prior_prob=None):
        """Performs linear discriminant analysis.

        Parameters
        ----------
        data_train: `ndarray`
            Training data (2-D array).
        classlabels: `ndarray`
            Class labels of the training data (1-D array).
        prior_prob: `list`
            List of prior class probabilities (optional).

        Returns
        -------
        w: `ndarray`
            Discovered linear coefficients (2-D array).
        """
        n, m = np.shape(data_train)
        classlabel = np.unique(classlabels)
        n_classes = len(classlabel)
        n_group = np.empty(n_classes)  # Group counts
        mean_group = np.empty((n_classes, m))  # Group sample means
        pooled_cov = np.zeros((m, m))  # Pooled covariance
        w = np.empty((n_classes, m + 1))  # model coefficients

        for i in range(n_classes):
            # Establish location and size of each class
            group = np.where(classlabels == classlabel[i])[0]
            n_group[i] = len(group)

            # Calculate group mean vectors
            mean_group[i] = np.mean(data_train[group, :], axis=0)

            # Accumulate pooled covariance information
            pooled_cov += ((n_group[i] - 1) / (n - n_classes)) * np.cov(data_train[group, :].T)

        if prior_prob is None:
            # Use the sample probabilities
            prior_prob = n_group / n

        # Loop over classes to calculate linear discriminant coefficients
        for i in range(n_classes):
            # Intermediate calculation for efficiency
            tmp = np.linalg.lstsq(pooled_cov.T, mean_group[i, :].T, rcond=None)[0].T

            # Constant
            w[i, 0] = -0.5 * np.matmul(tmp, mean_group[i, :]) + np.log(prior_prob[i])

            # Linear
            w[i, 1:np.shape(w)[1]] = tmp

        return w


if __name__ == "__main__":

    cwd = os.getcwd()

    # Read BCI Configuration
    config_file = cwd + '/bci-config.json'
    with open(config_file) as json_file:
        config = json.load(json_file)

    # ------------- Subject specific variables -------------
    motor_mode = config['gui-input-settings']['motor-mode']
    dimension = config['gui-input-settings']['dimension-mode']
    subject_id = config['gui-input-settings']['subject-id']
    session = str(config['gui-input-settings']['n-session'])
    run = str(config['gui-input-settings']['n-run'])
    # ------------------------------------------------------

    xdf_to_mat.xdf_to_mat(config)  # convert .xdf to .mat


    file_name = subject_id  + '_ses' + session + '_run' + run+ '_' + motor_mode + '_' + dimension

    root_dir = cwd + '/SubjectData/' + subject_id + '/'
    dir_out = root_dir + '/../current/'
    file_path = root_dir + file_name

    # Load eeg data
    data_mat = scipy.io.loadmat(file_path)['data'].T
    class_labels = data_mat[0, :]
    eeg_signal = data_mat[1:, :]

    # Compute CSP filter and LDA coefficients and save as .mat files
    csp_lda_obj = CSPAndLDA(eeg=eeg_signal, labels=class_labels, bci_config=config)

    csp = csp_lda_obj.compute_csp()
    scipy.io.savemat(root_dir + 'CSP_' + file_name + '.mat', {'csp_filter': csp})
    scipy.io.savemat(dir_out + 'csp' + '.mat', {'csp_filter': csp})

    lda_coeff = csp_lda_obj.compute_lda(csp)
    scipy.io.savemat(root_dir + 'LDA_' + file_name + '.mat', {'W': lda_coeff})
    scipy.io.savemat(dir_out + 'lda' + '.mat', {'W': lda_coeff})
