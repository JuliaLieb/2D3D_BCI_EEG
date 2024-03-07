import pyxdf
import matplotlib.pyplot as plt
import numpy as np
import os
import json
import mne
from mne.datasets import misc
import matplotlib.pyplot as plt


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

'''
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


'''
def ex_plt(xdf_file_path):

    data, header = pyxdf.load_xdf(xdf_file_path)

    for stream in data:
        y = stream['time_series']

        if isinstance(y, list):
            # list of strings, draw one vertical line for each marker
            '''for timestamp, marker in zip(stream['time_stamps'], y):
                plt.axvline(x=timestamp)
                print(f'Marker "{marker[0]}" @ {timestamp:.2f}s') '''
        elif isinstance(y, np.ndarray):
            # numeric data, draw as lines
            plt.plot(stream['time_stamps'], y)
        else:
            raise RuntimeError('Unknown stream format')

    plt.show()

def plt_eeg(eeg_time, eeg_data):
    plt.plot(eeg_time, eeg_data)
    plt.show()



def extract_lst(lst):
    return [item[0] for item in lst]

def get_sequence_timing(stream_marker):
    marker_list = stream_marker.get('time_series')
    marker_list = extract_lst(marker_list)

    marker_time = stream_marker.get('time_stamps')

    # index_trial_r = marker_list.index('Start_of_Trial_r')
    cue_sequence = []
    for i in marker_list:
        if i == 'Start_of_Trial_r':
            cue_sequence.append('r')
        elif i == 'Start_of_Trial_l':
            cue_sequence.append('l')
    index_cue = [i for i, x in enumerate(marker_list) if x == 'Cue']
    index_end = [i for i, x in enumerate(marker_list) if x == 'End_of_Trial']
    cue_start = [marker_time[i] for i in index_cue]
    cue_end = [marker_time[i] for i in index_end]

    return cue_sequence, cue_start, cue_end

def get_cue_fb(stream_fb_lda, cue_start, cue_end):
    distance_list = stream_fb_lda.get('time_series')
    distance_time = stream_fb_lda.get('time_stamps')
    fb_distance = []
    fb_corr = []

    for cue in range(len(cue_start)):
        distance = []
        correct = []
        index = 0
        for i in distance_time:
            if i >= cue_start[cue] and i < cue_end[cue]:
                distance.append(distance_list[index][1])
                correct.append(distance_list[index][0])
                index +=1
            else:
                index += 1
        fb_distance.append(distance)
        fb_corr.append(correct)

    return fb_distance, fb_corr

def get_eeg_channel_data(stream_eeg, channel):
    eeg_data = stream_eeg.get('time_series').T
    eeg_time = stream_eeg.get('time_stamps')
    channel_data = eeg_data[channel]
    return eeg_time, channel_data

if __name__ == "__main__":

    cwd = os.getcwd()

    # Read BCI Configuration
    #config_file = cwd + '/bci-config.json'
    config_file = 'C:/2D3D_BCI_EEG/bci-config.json'
    with open(config_file) as json_file:
        config = json.load(json_file)
    # ------------- Subject specific variables -------------
    motor_mode = config['gui-input-settings']['motor-mode']
    dimension = config['gui-input-settings']['dimension-mode']
    subject_id = config['gui-input-settings']['subject-id']
    session = str(config['gui-input-settings']['n-session'])
    run = str(config['gui-input-settings']['n-run'])
    # ------------------------------------------------------

    root_dir = cwd + './SubjectData/'

    file_name = subject_id + '_ses' + session + '_run' + run + '_' + motor_mode + '_' + dimension
    #xdf_file_path = root_dir + subject_id + '/' + file_name + '.xdf'
    xdf_file_path = 'C:/2D3D_BCI_EEG/SubjectData/S5/' + file_name + '.xdf'

    stream_eeg, stream_marker, stream_fb_lda, stream_fb_erds = load_xdf(xdf_file_path,
                                                                        config['general-settings']['lsl-streams'])

    #distance_list = extract_lst(distance_list)

    cue_sequence, cue_start, cue_end = get_sequence_timing(stream_marker)
    fb_distance, fb_corr = get_cue_fb(stream_fb_lda, cue_start, cue_end)


    # Test
    """
    streams, header = pyxdf.load_xdf(xdf_file_path)
    data = streams[0]["time_series"].T
    assert data.shape[0] == 36  # four raw EEG plus one stim channel
    data[:4:2] -= data[1:4:2]  # subtract (rereference) to get two bipolar EEG
    data = data[::2]  # subselect
    data[:2] *= (1e-6 / 50 / 2)  # uV -> V and preamp gain
    sfreq = float(streams[0]["info"]["nominal_srate"][0])
    info = mne.create_info(3, sfreq, ["eeg", "eeg", "stim"])
    raw = mne.io.RawArray(data, info)
    #raw.plot(scalings=dict(eeg=100e-6), duration=1, start=14)
    """

    #"""
    eeg_time, eeg_data = get_eeg_channel_data(stream_eeg, 2)
    plt_eeg(eeg_time, eeg_data)
    ex_plt(xdf_file_path)
    #"""

    """
    x = int(True)
    print(x, ' This is just a test integer!')
    """
