import pyxdf
import matplotlib.pyplot as plt
import numpy as np
import os
import json
import mne
from mne.datasets import misc


def load_xdf(xdf_file, lsl_config):

    streams, fileheader = pyxdf.load_xdf(xdf_file)
    streams_info = []

    for stream in streams:
        streams_info.append(stream['info']['name'][0])

    streams_info = np.array(streams_info)

    eeg_pos = np.where(streams_info == lsl_config['eeg']['name'])[0][0]
    marker_pos = np.where(streams_info == lsl_config['marker']['name'])[0][0]
    fb_lda_pos = np.where(streams_info == lsl_config['fb-lda']['name'])[0][0]
    fb_erds_pos = np.where(streams_info == lsl_config['fb-erds']['name'])[0][0]

    return streams[eeg_pos], streams[marker_pos], streams[fb_lda_pos], streams[fb_erds_pos]

def mne_plt(xdf_file_path):

    streams, header = pyxdf.load_xdf(xdf_file_path)
    data = streams[0]["time_series"].T
    assert data.shape[0] == 5  # four raw EEG plus one stim channel
    data[:4:2] -= data[1:4:2]  # subtract (rereference) to get two bipolar EEG
    data = data[::2]  # subselect
    data[:2] *= (1e-6 / 50 / 2)  # uV -> V and preamp gain
    sfreq = float(streams[0]["info"]["nominal_srate"][0])
    info = mne.create_info(3, sfreq, ["eeg", "eeg", "stim"])
    raw = mne.io.RawArray(data, info)
    raw.plot(scalings=dict(eeg=100e-6), duration=1, start=14)



def ex_plt(xdf_file_path):

    data, header = pyxdf.load_xdf(xdf_file_path)

    for stream in data:
        y = stream['time_series']

        if isinstance(y, list):
            # list of strings, draw one vertical line for each marker
            for timestamp, marker in zip(stream['time_stamps'], y):
                plt.axvline(x=timestamp)
                print(f'Marker "{marker[0]}" @ {timestamp:.2f}s')
        elif isinstance(y, np.ndarray):
            # numeric data, draw as lines
            plt.plot(stream['time_stamps'], y)
        else:
            raise RuntimeError('Unknown stream format')

    plt.show()


if __name__ == "__main__":

    cwd = os.getcwd()

    # Read BCI Configuration
    config_file = cwd + '/../bci-config.json'
    with open(config_file) as json_file:
        config = json.load(json_file)
    # ------------- Subject specific variables -------------
    motor_mode = config['gui-input-settings']['motor-mode']
    dimension = config['gui-input-settings']['dimension-mode']
    subject_id = config['gui-input-settings']['subject-id']
    session = str(config['gui-input-settings']['n-session'])
    run = str(config['gui-input-settings']['n-run'])
    # ------------------------------------------------------

    root_dir = cwd + '/../SubjectData/'

    file_name = subject_id + '_ses' + session + '_run' + run + '_' + motor_mode + '_' + dimension
    xdf_file_path = root_dir + subject_id + '/' + file_name + '.xdf'

    stream_eeg, stream_marker, stream_fb_lda, stream_fb_erds = load_xdf(xdf_file_path, config['general-settings']['lsl-streams'])

    test = False
    #mne_plt(xdf_file_path)




