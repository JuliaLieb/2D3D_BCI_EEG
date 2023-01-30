"""
Simulates EEG data (using the signal server) and streams the simulated data via LSL.
"""

import json
import numpy as np
import os
import pytiaclient
from pylsl import StreamInfo, StreamOutlet, local_clock
import subprocess
import time

import bciutils

data = []


def receive_data_from_tia():
    """Receives data from the TIA client.
    """
    client.start_data()
    global data
    while True:
        data = client.get_data_chunk(blocking=True)[0]


if __name__ == "__main__":
    cwd = os.getcwd()

    # Start TiA server
    os.chdir('signalserver')
    subprocess.run(["signalserver_eegsim.bat"])

    # Connect to TiA server
    TCP_IP = "127.0.0.1"
    TCP_PORT = 9000
    client = pytiaclient.TIAClient()
    client.connect(TCP_IP, TCP_PORT)
    meta_info = client._metainfo

    # Get info about the signal
    s_rate = int(meta_info["signals"][0]["samplingRate"])
    n_channels = int(meta_info["signals"][0]["numChannels"])
    block_size = int(meta_info["signals"][0]["blockSize"])

    # Read config file
    os.chdir(cwd)
    config_file = cwd + '/../bci-config.json'
    with open(config_file) as json_file:
        config = json.load(json_file)

    # Create a LSL stream and outlet for eeg data
    eeg_stream_stgs = config['general-settings']['lsl-streams']['eeg']
    info = StreamInfo(name=eeg_stream_stgs['name'], channel_count=n_channels, nominal_srate=s_rate,
                      channel_format='float32', source_id=eeg_stream_stgs['id'])
    outlet = StreamOutlet(info)

    # Start TiA data transmission
    bciutils.threading.Thread(target=receive_data_from_tia).start()

    # Send data via LSL
    start_time = local_clock()
    sent_samples = 0
    pos = 0
    max_samples = 100000

    while True:
        if not data:
            time.sleep(0.01)
            continue
        else:
            elapsed_time = local_clock() - start_time
            required_samples = int(s_rate * elapsed_time) - sent_samples
            for sample_ix in range(required_samples):
                my_sample = np.array(data)[:, pos]
                outlet.push_sample(my_sample)

                if pos < block_size - 1:
                    pos += 1
                else:
                    pos = 0

            sent_samples += required_samples
            if sent_samples > max_samples:
                sent_samples = 0
                start_time = local_clock()
            time.sleep(0.01)

    client.stop_data()
    client.close()
