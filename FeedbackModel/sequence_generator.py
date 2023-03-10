"""
Creates sequences with tasks repeated randomly and saves them as text file.
"""

import os
import random


def create_sequence(trials, my_tasks):
    """Creates a sequence with tasks repeated randomly.

    Parameters
    ----------
    trials: `int`
        The number of trials for each task.
    my_tasks: `list`
        The list of tasks.

    Returns
    -------
    my_sequence: `list`
        A list with the tasks repeated in random order.
    """
    my_sequence = []

    for t in range(trials):
        for i in range(len(my_tasks)):
            my_sequence.append(my_tasks[i])

    random.shuffle(my_sequence)
    return my_sequence


def sequence_generator(subject_id, tasks_per_run, n_run, n_session, motor_mode, dimension_mode):
    tasks = ["r", "l"]  # left and right hand

    # current subject
    directory = "SubjectData\\current\\"
    file_object = open(directory + "run_" + str(n_run) + ".txt", "w")

    # subject backup recording
    directory_backup = "SubjectData\\" + subject_id + "\\"
    file_backup = open(directory_backup + "SEQ_" + subject_id + '_ses' + str(n_session) + '_run' + str(
        n_run) + '_' + motor_mode + '_' + dimension_mode + ".txt", "w")

    # Check existence of paths and files
    if not os.path.exists(directory):
        os.makedirs(directory)
    if not os.path.exists(directory_backup):
        os.makedirs(directory_backup)

    if n_run == 1:
        t = 10  # for classification run: always 10 runs per condition (20 in total)
    else:
        t = int(tasks_per_run/2)
    sequence = create_sequence(t, tasks)

    for trial in sequence:
        file_object.write(trial + "\n")
        file_backup.write(trial + "\n")
