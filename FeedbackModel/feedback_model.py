"""
EEG Feedback Model
Performs classification and calculates erds-values for online-BCIs.
"""

import json
import numpy as np
import os
import scipy.io

import bciutils

if __name__ == "__main__":

    cwd = os.getcwd()
    config_file = cwd + '/bci-config.json'

    # Read BCI Configuration
    with open(config_file) as json_file:
        config = json.load(json_file)

    # Initialize the BCI model
    bci_model = bciutils.BCI(config)

    # Load CSP and LDA coefficients
    csp_filter = scipy.io.loadmat(cwd + '/SubjectData/current/csp.mat')['csp_filter']
    lda_coef = scipy.io.loadmat(cwd + '/SubjectData/current/lda.mat')['W']

    s_rate_half = bci_model.sample_rate / 2

    # Define bandpass for classification unit
    bandpass_settings_cl = config['feedback-model-settings']['bandpass']
    fstop = [freq / s_rate_half for freq in bandpass_settings_cl['fstop']]
    fpass = [freq / s_rate_half for freq in bandpass_settings_cl['fpass']]
    bandpass_cl = bciutils.Bandpass(order=bandpass_settings_cl['order'], fstop=fstop, fpass=fpass,
                                    n=bci_model.n_enabled_channels)

    # Define bandpass for ERDS unit
    bandpass_settings_erds = config['feedback-model-settings']['bandpass-erds']
    fstop_erds = [freq / s_rate_half for freq in bandpass_settings_erds['fstop']]
    fpass_erds = [freq / s_rate_half for freq in bandpass_settings_erds['fpass']]
    bandpass_erds = bciutils.Bandpass(order=bandpass_settings_erds['order'], fstop=fstop_erds, fpass=fpass_erds,
                                      n=bci_model.n_enabled_channels)

    # Define log band power unit
    log_band_power_unit = bciutils.LogBandPower(window_length=1 * bci_model.sample_rate,
                                                n=np.shape(csp_filter)[0])

    # Define BCI Core
    bci_model.bci_core = bciutils.BCICore(sample_rate=bci_model.sample_rate,
                                          bandpass_cl=bandpass_cl,
                                          bandpass_erds=bandpass_erds,
                                          csp=csp_filter, lda=lda_coef, log_band_power=log_band_power_unit)

    # Start the feedback loop. It will run unitl the script is stopped by the user
    bci_model.start_feedback_loop()
