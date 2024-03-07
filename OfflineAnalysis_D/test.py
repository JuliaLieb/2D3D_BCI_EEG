import os
import scipy.io
import json
import matplotlib.pyplot as plt
import numpy as np

from bci_modules import Bandpass


cwd = os.getcwd()
root_dir = cwd + '/../../pilot-study/'

data_eeg = scipy.io.loadmat(root_dir + '/eeg.mat')['eeg'].T

classlabels = np.where((data_eeg[0, :] == 121) | (data_eeg[0, :] == 122))[0]

config_file = root_dir + '/bci-config.json'
with open(config_file) as json_file:
    config = json.load(json_file)

s_rate_half = config['eeg-settings']['sample-rate'] / 2

bandpass_settings_erds = config['feedback-model-settings']['bandpass-erds']
fstop_erds = [freq / s_rate_half for freq in bandpass_settings_erds['fstop']]
fpass_erds = [freq / s_rate_half for freq in bandpass_settings_erds['fpass']]
bp = Bandpass(order=bandpass_settings_erds['order'], fstop=fstop_erds, fpass=fpass_erds, n=32)

x = data_eeg[1:33, classlabels[0]-1500:classlabels[0]+2500].T
# y = bp.bandpass_filter(x)
# plt.plot(y[:, 25])

y = np.zeros((1, 32))
for i in range(np.shape(x)[0]):
    y = np.append(y, bp.bandpass_filter(x[i:i+1, :]), axis=0)
    # y = bp.bandpass_filter(x[i:i+1, :])

plt.plot(y[1:, 25])
# plt.plot(x[:, 25])

plt.show()

print("")


