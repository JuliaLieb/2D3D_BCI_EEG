"""
Includes all classes needed for performing online eeg analyis.
"""

from enum import Enum
import math
import numpy as np
from pylsl import StreamInfo, StreamInlet, StreamOutlet, resolve_stream, local_clock
from scipy import signal
import threading


class BCIState(Enum):
    """Enum class for definition of the BCI states.
    """

    START = 0
    REFERENCE = 1
    CUE = 2
    FEEDBACK = 3
    BREAK = 4
    SLEEP = 5


class ERDSMode(str, Enum):
    """Enum class for definition of the ERDS calculation mode.

        AVERAGE: the average of all channels (per roi) is used for the erds
        SINGLE:  only a single channel (per roi, defined in bci-config.json) is considered for erds calculation.
    """

    AVERAGE = 'average'
    SINGLE = 'single'


class BCI:
    """Main unit of the feedback loop.

    Takes care of receiving and sending data from/to LSL streams and manages the computation of the feedback.

    Parameters
    ----------
    bci_config: `dict`
        Settings for the feedback loop.

    Other Parameters
    ----------------
    state: `enum`
        Current state of the BCI.
    bci_core: `BCICore instance`
        Signal processing unit.
    stream_eeg: `str`
        Name of the eeg LSL stream.
    stream_marker: `str`
        Name of the marker LSL stream from unity.
    inlet_eeg: `StreamInlet`
        Inlet of the eeg stream.
    stream_fb_cl: `str`
        Name of the feedback stream for the class labels and distance.
    stream_fb_erds: `str`
        Name of the feedback stream for the ERDS values.
    thread_classification: `Thread object`
        Thread object for performing the classification.
    thread_erds: `Thread object`
        Thread object for computation of ERDS values.
    thread_marker: `Thread object`
        Thread object for receiving the markers.
    sample_rate: `int`
        Sample rate of the eeg signal.
    idx_start_ref: `int`
        Start index for the computation of the mean eeg in the reference period.
    n_enabled_channels: `int`
        Number of channels used for the feedback calculation.
    idx_enabled_channels: `ndarray`
        1-D Array of indexes of enabled channels.
    channel_to_roi_map:  `ndarray`
        2-D Array of indexes of channels (per ROI) to use for the computation of ERDS values.
    n_roi: `int`
        Number of region of interests.
    data_ref: `ndarray`
        2-D array of eeg data during the reference period.
    data_ref_mean: `ndarray`
        2-D array of mean eeg reference data for each channel.
    """

    def __init__(self, bci_config):
        self.state = BCIState.START
        self.bci_core = None

        self.stream_eeg = bci_config['general-settings']['lsl-streams']['eeg']
        self.stream_marker = bci_config['general-settings']['lsl-streams']['marker']
        self.inlet_eeg: None

        self.stream_fb_cl = bci_config['general-settings']['lsl-streams']['fb-lda']
        self.stream_fb_erds = bci_config['general-settings']['lsl-streams']['fb-erds']

        self.thread_classification = threading.Thread(target=self.__compute_classification)
        self.thread_erds = threading.Thread(target=self.__compute_erds)
        self.thread_marker = threading.Thread(target=self.start_feedback_loop)

        self.sample_rate = 0
        self.idx_start_ref = 0
        self.n_enabled_channels = 0
        self.idx_enabled_channels = 0
        self.channel_to_roi_map = []
        self.n_roi = bci_config['feedback-model-settings']['erds']['number-roi']

        self.data_ref = None
        self.data_ref_mean = None

        self.__resolve_eeg_stream()
        self.__select_enabled_channels(bci_config['eeg-settings']['channels'],
                                       bci_config['feedback-model-settings']['erds'])

    def __del__(self):
        if self.thread_erds.is_alive():
            self.thread_erds.join()
        if self.thread_classification.is_alive():
            self.thread_classification.join()
        if self.thread_marker.is_alive():
            self.thread_marker.join()

    def __resolve_eeg_stream(self):
        """Resolves the eeg stream and extracts some information.
        """

        self.inlet_eeg = self.resolve_lsl_stream(name=self.stream_eeg['name'])

        info_eeg = self.inlet_eeg.info()
        print(info_eeg.as_xml())

        self.n_enabled_channels = int(info_eeg.channel_count())
        self.sample_rate = int(info_eeg.nominal_srate())
        self.idx_start_ref = int(info_eeg.nominal_srate() / 2)

    def __select_enabled_channels(self, channel_settings, erds_settings):
        """Selects which eeg channels are used for the computation of the feedback.

        Parameters
        ----------
        channel_settings: `dict`
            Settings for the eeg channels (index, mapping to ROI, enabled).
        erds_settings: `dict`
            Settings for the calculation of ERDS values.
        """

        # Read all channel settings
        list_is_channel_enabled = np.zeros((self.n_enabled_channels,), dtype=bool)
        list_roi_of_channel = np.zeros((self.n_enabled_channels,), dtype=int)
        list_id_of_channel = np.zeros((self.n_enabled_channels,), dtype=int)

        cnt = 0
        for ch in channel_settings:
            obj = channel_settings[ch]
            list_is_channel_enabled[cnt] = obj['enabled']
            list_roi_of_channel[cnt] = obj['roi']
            list_id_of_channel[cnt] = obj['id']
            cnt += 1

        # Save the amount and indexes of channels used for the classification
        self.idx_enabled_channels = np.where(list_is_channel_enabled)[0]
        self.n_enabled_channels = np.shape(self.idx_enabled_channels)[0]

        # Save the indexes of channels used for the ERDS computation
        list_roi_of_channel = list_roi_of_channel[self.idx_enabled_channels]
        list_id_of_channel = list_id_of_channel[self.idx_enabled_channels]

        if erds_settings['mode'] == ERDSMode.AVERAGE:
            for roi in range(1, self.n_roi + 1):
                self.channel_to_roi_map.append(np.where(list_roi_of_channel == roi)[0])
        elif erds_settings['mode'] == ERDSMode.SINGLE:
            for ch in erds_settings['single-mode-channels']:
                self.channel_to_roi_map.append(np.where(list_id_of_channel == ch)[0])

    def __reset_buffer(self):
        """Resets the buffer for the eeg data during the reference period after each trial.
        """

        self.data_ref = np.zeros((1, self.n_enabled_channels))
        self.data_ref_mean = np.zeros((1, self.n_enabled_channels))
        self.data_ref_mean[:] = np.nan

    def __compute_erds(self):
        """Computes ERDS values during each trial.

        During the reference period eeg data is stored in a buffer. During the feedback period the ERDS values are
        calculated.
        """

        # important that this thread has its own instance of inlet eeg
        inlet_eeg = self.resolve_lsl_stream(name=self.stream_eeg['name'])

        stream_info = StreamInfo(name=self.stream_fb_erds['name'], channel_count=self.n_roi, nominal_srate=0,
                                 channel_format='float32', source_id=self.stream_fb_erds['id'])
        outlet_fb_erds = StreamOutlet(stream_info)

        self.__reset_buffer()
        erds_per_roi = np.zeros((self.n_roi,))

        while True:
            sample, timestamp = inlet_eeg.pull_sample()
            sample = np.expand_dims(sample, axis=0)[:, self.idx_enabled_channels]

            if self.state == BCIState.REFERENCE:
                self.data_ref = np.append(self.data_ref, np.square(self.bci_core.bandpass_erds.bandpass_filter(sample)),
                                          axis=0)
            elif self.state == BCIState.FEEDBACK:
                erds_a = np.square(self.bci_core.bandpass_erds.bandpass_filter(sample))

                # May happen if the state changed to BREAK in the meantime (this means the buffer was reset)
                if np.any(np.isnan(erds_a)) or np.any(np.isnan(self.data_ref_mean)):
                    continue

                erds = np.divide(-(self.data_ref_mean - erds_a), self.data_ref_mean)

                # Compute mean erds over each roi
                for roi in range(self.n_roi):
                    erds_per_roi[roi] = np.mean(erds[0, self.channel_to_roi_map[roi]])

                outlet_fb_erds.push_sample(erds_per_roi, local_clock())

            elif self.state == BCIState.START:
                self.bci_core.bandpass_erds.bandpass_filter(sample)

    def __compute_classification(self):
        """Performs classification of the eeg data.

        During the Feedback period the class label and the distance is computed.
        """

        stream_info = StreamInfo(name=self.stream_fb_cl['name'], channel_count=2, nominal_srate=0,
                                 channel_format='float32', source_id=self.stream_fb_cl['id'])
        outlet_fb_cl = StreamOutlet(stream_info)

        while True:
            sample, timestamp = self.inlet_eeg.pull_sample()
            sample = np.expand_dims(sample, axis=0)[:, self.idx_enabled_channels]

            if self.state == BCIState.FEEDBACK:
                y_bp = self.bci_core.bandpass_cl.bandpass_filter(sample)
                y_csp = self.bci_core.csp_filter(y_bp)
                y_lbp = self.bci_core.log_band_power.compute_log_band_power(y_csp)

                label, distance = self.bci_core.lda_predict(y_lbp)
                outlet_fb_cl.push_sample([label - 1, distance], local_clock())
            elif self.state == BCIState.START:
                self.bci_core.bandpass_cl.bandpass_filter(sample)

    def start_feedback_loop(self):
        """Manages the feedback loop.

        Starts the classification and ERDS thread and receives the markers from unity
        in order to set the BCI state accordingly.
        """

        inlet_marker = self.resolve_lsl_stream(name=self.stream_marker['name'])

        self.thread_classification.start()
        self.thread_erds.start()

        # Feed the bandpass filter during the first 3 seconds after starting the feedback model
        # (because those first values are rubbish)
        start_time = local_clock()
        while self.state == BCIState.START:
            if int(local_clock() - start_time) > 3:
                self.state = BCIState.SLEEP

        while True:
            if inlet_marker is None:
                continue
            marker, timestamp = inlet_marker.pull_sample()
            if marker is None:
                continue

            if marker[0] == 'Reference':
                self.state = BCIState.REFERENCE
            elif marker[0] == 'Cue':
                self.state = BCIState.CUE
                # Calculate mean erds values over reference period
                if np.shape(self.data_ref)[0] > 1:
                    self.data_ref_mean = np.mean(np.delete(self.data_ref, 0, 0)[self.idx_start_ref:, :],
                                                 axis=0)
                else:
                    print("ERROR no ERDS values are calculated")
            elif marker[0] == 'Feedback':
                self.state = BCIState.FEEDBACK
            elif marker[0] == 'End_of_Trial':
                self.state = BCIState.BREAK
                self.bci_core.reset_buffer()
                self.__reset_buffer()

    @staticmethod
    def resolve_lsl_stream(name):
        """Opens an inlet for a LSL stream.

        Parameters
        ----------
        name: `str`
            Name of the LSL stream.

        Returns
        -------
        inlet: `StreamInlet`
            Inlet for the LSL stream.
        """

        stream = resolve_stream("name", name)
        inlet = StreamInlet(stream[0])
        return inlet


class BCICore:
    """Signal processing unit.

    Includes members and methods for filtering data, for classification and for calculation of the LDA distance.

    Parameters
    ----------
    sample_rate: `int`
        Sample rate of the eeg signal.
    bandpass_cl: `Bandpass instance`
        Bandpass filtering unit for the classification.
    bandpass_erds: `Bandpass instance`
        Bandpass filtering unit for the ERDS calculation.
    csp: `ndarray`
        Common spatial pattern (2-D array).
    lda: `ndarray`
        Linear discriminant analysis coefficients (2-D array).
    log_band_power: `LogBandPower instance`
        Unit for computing the log band power.

    Other Parameters
    ----------------
    label: `int`
        Current computed class label.
    label_buffer: `ndarray`
        1-D array of past class labels.
    is_class_buffer: `ndarray`
        1-D array buffer used for the distance calculation.
    label_idx: `int`
        Current index for the buffered labels (label_buffer). The class label at this index represents the class label
        calculated a minute ago.
    """

    def __init__(self, sample_rate, bandpass_cl, bandpass_erds, csp, lda, log_band_power):
        self.sample_rate = sample_rate
        self.bandpass_cl = bandpass_cl
        self.bandpass_erds = bandpass_erds
        self.CSP = csp
        self.LDA = lda
        self.log_band_power = log_band_power

        self.label = None
        self.label_buffer = None
        self.is_class_buffer = None
        self.label_idx = 0

        self.reset_buffer()

        np.seterr(invalid='ignore')  # ignores inf values (in matmul() in classification())
        np.seterr(divide='ignore')  # ignores division by zero (may happen in log_band_power())

    def reset_buffer(self):
        """Clears the buffered values after every trial.
        """

        self.label_buffer = np.zeros((self.sample_rate,), dtype=int)
        self.label_idx = 0
        self.is_class_buffer = np.zeros((2,), dtype=int)

    def csp_filter(self, x):
        """Filters the signal with the CSP model.

        Parameters
        ----------
        x: `ndarray`
            Band passed eeg data of all enabled channels.

        Returns
        -------
        return: `ndarray`
            CSP filtered input array.
        """

        return np.matmul(x, self.CSP.T)

    def lda_predict(self, x):
        """Predicts the class of the data with linear discriminant analysis.

        Parameters
        ----------
        x: `ndarray`
            1-D array.

        Returns
        -------
        label: `int`
            Class label.
        distance:  `float`
            LDA distance.
        """

        x_conc = np.append(np.ones([np.shape(x)[0], 1]), x, axis=1)
        x_mat = np.matmul(x_conc, self.LDA.T)
        linear_scores = np.divide(np.multiply(x_mat, 100),
                                  np.max(np.abs(x_mat)))
        self.label = np.nanargmax(linear_scores, axis=1)[0] + 1
        label, distance = self.lda_disctance_calculation()

        return label, distance

    def lda_disctance_calculation(self):
        """Computes the distance (linear distance function) of the currently classified value and smoothes outliers.

        Returns
        -------
        class_label: `int`
            Optimized class label.
        distance:  `float`
            LDA distance.
        """

        # linear distance function
        # distance equals length of feedback bar -> in VR intesity of outline glow
        is_class_1 = 1 * (self.label == 1) - 1 * (self.label_buffer[self.label_idx] == 1) + self.is_class_buffer[0]
        is_class_2 = 1 * (self.label == 2) - 1 * (self.label_buffer[self.label_idx] == 2) + self.is_class_buffer[1]
        class_label = np.argmax([is_class_1, is_class_2], axis=0) + 1

        distance = self.is_class_buffer[class_label - 1] / self.sample_rate

        self.label_buffer[self.label_idx] = self.label
        self.is_class_buffer = np.array([is_class_1, is_class_2])

        if self.label_idx < self.sample_rate - 1:
            self.label_idx += 1
        else:
            self.label_idx = 0

        return class_label, distance


class Bandpass:
    """Bandpass unit.

    Holds parameters and methods for bandpass filtering.

    Parameters
    ----------
    order: `int`
        The order of the filter.
    fpass: `list`
        Frequencies of the filter.
    n: `int`
        Number of eeg channels.

    Other Parameters
    ----------------
    sos: `ndarray`
        Second-order sections representation of the filter.
    zi0: `ndarray`
        Initial conditions for the filter delay.
    zi: `ndarray`
        Current filter delay values.
    """

    def __init__(self, order, fstop, fpass, n):
        self.order = order
        self.fstop = fstop
        self.fpass = fpass
        self.n = n
        self.sos = None
        self.zi0 = None
        self.zi = None

        self.__init_filter()

    def __init_filter(self):
        """Computes the second order sections of the filter and the initial conditions for the filter delay.
        """

        self.sos = signal.iirfilter(int(self.order / 2), self.fpass, btype='bandpass', ftype='butter',
                                    output='sos')

        zi = signal.sosfilt_zi(self.sos)

        if self.n > 1:
            zi = np.tile(zi, (self.n, 1, 1)).T
        self.zi0 = zi.reshape((np.shape(self.sos)[0], 2, self.n))
        self.zi = self.zi0

    def bandpass_filter(self, x):
        """Bandpass filters the input array.

        Parameters
        ----------
        x: `ndarray`
            Raw eeg data.

        Returns
        -------
        y: `int`
            Band passed data.
        """

        y, self.zi = signal.sosfilt(self.sos, x, zi=self.zi, axis=0)
        return y


class LogBandPower:
    """Log band power unit.

    Holds parameters and methods for computing the log band power of a signal.

    Parameters
    ----------
    window_length: `int`
        Length of the window.
    n: `int`
        Number of channels.

    Other Parameters
    ----------------
    a: `int`
        The denominator coefficient.
    b: `ndarray`
        The numerator coefficient vector (1-D array).
    zi: `ndarray`
        Conditions for lfilter for step response steady-state.
    """

    def __init__(self, window_length, n):
        self.window_length = window_length
        self.n = n
        self.a = None
        self.b = None
        self.zi = None

        self.__init_conditions()

    def __init_conditions(self):
        """Initializes the coefficients for the filter and the initial conditions for the filter delay.
        """

        window_samples = math.floor(self.window_length)
        self.b = 1 / window_samples * np.ones((1, window_samples))
        self.a = 1

        zi = signal.lfilter_zi(self.b[0], self.a)
        if self.n > 1:
            zi = np.tile(zi, (self.n, 1)).T
        self.zi = zi

    def compute_log_band_power(self, x):
        """Computes the logarithmic band power of the input signal.

        Parameters
        ----------
        x: `ndarray`
            Input data.

        Returns
        -------
        y: `ndarray`
            The log band power of the input data.
        """

        x_filt, self.zi = signal.lfilter(self.b[0], self.a, np.square(np.abs(x)), zi=self.zi, axis=0)

        return np.log10(x_filt)
