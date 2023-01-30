"""
Update BCI Configuration
Functions to update bci-config.json with GUI input
"""

import json
import numpy as np
import os

def update_bci_config(subject_id, total_runs, tasks_per_run, n_run, n_session, motor_mode, fb_mode, erds_mode, dimension_mode):

    cwd = os.getcwd()
<<<<<<< HEAD:FeedbackModel/bci_config.py
    config_file = cwd + '/bci-config.json'

    with open(config_file) as json_file:
        current_config = json.load(json_file)

    return current_config


def update_bci_config(subject_id, total_runs, tasks_per_run, n_run, n_session, motor_mode, fb_mode, erds_mode,
                      dimension_mode):
    cwd = os.getcwd()
    config_file = cwd + '/bci-config.json'
    file_name = subject_id + '_ses' + str(n_session) + '_run' + str(
        n_run) + '_' + motor_mode + '_' + dimension_mode + '-config.json'
    save_path = cwd + 'FeedbackModel/data/measurements/' + subject_id + '/'
=======
    config_file = cwd + '/../bci-config.json'
    #measurement_config_file = cwd + '/../FeedbackModel/data/current/subj-P' + subject_id + '/session'+ n_session + '_run'+ n_run + '_' + motor_mode + '_' + dimension_mode + '-config.json'

>>>>>>> parent of 6a33a90 (GUI improvements):FeedbackModel/update_bci_config.py

    # Read BCI Configuration
    with open(config_file) as json_file:
        config = json.load(json_file)
        config['gui-input-settings']['subject-id'] = subject_id
        config['gui-input-settings']['total-runs'] = total_runs
        config['gui-input-settings']['n-per-task'] = tasks_per_run/2
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


