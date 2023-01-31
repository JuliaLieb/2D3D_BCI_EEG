"""
BCI Configuration
Functions to update bci-config.json with GUI input and to save in measurement folder for subject
"""

import json
import os


def read_bci_config():
    cwd = os.getcwd()
    config_file = cwd + '/bci-config.json'

    with open(config_file) as json_file:
        current_config = json.load(json_file)

    return current_config


def update_bci_config(subject_id, tasks_per_run, n_run, n_session, motor_mode, fb_mode, erds_mode,
                      dimension_mode):
    cwd = os.getcwd()
    config_file = cwd + '/bci-config.json'
    file_name = 'CONFIG_' + subject_id + '_ses' + str(n_session) + '_run' + str(
        n_run) + '_' + motor_mode + '_' + dimension_mode + '.json'
    save_path = cwd + '\\SubjectData\\' + subject_id + '\\'

    # Read BCI Configuration
    with open(config_file) as json_file:
        config = json.load(json_file)
        config['gui-input-settings']['subject-id'] = subject_id
        config['gui-input-settings']['n-per-task'] = tasks_per_run
        config['gui-input-settings']['n-run'] = n_run
        config['gui-input-settings']['n-session'] = n_session
        config['gui-input-settings']['motor-mode'] = motor_mode
        config['gui-input-settings']['fb-mode'] = fb_mode
        config['feedback-model-settings']['erds']['mode'] = erds_mode
        config['gui-input-settings']['dimension-mode'] = dimension_mode

    # Remove old file
    os.remove(config_file)

    # Create new file with added data
    with open(config_file, 'w') as json_file:
        json.dump(config, json_file, indent=4)

    # Save config_file for measurement
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    save_config_file = save_path + file_name
    with open(save_config_file, 'w') as json_file:
        json.dump(config, json_file, indent=4)
